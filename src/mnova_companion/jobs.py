"""Durable job receipts and a conservative single-writer native lease."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator

from .contracts import Hash, Identifier, JobState, ShortText, StrictModel
from .execution import (
    PHASES,
    BuildProfile,
    Dispatch,
    EvidenceFile,
    ExecutionIdentity,
    ExecutorHandshake,
    Receipt,
    admit_fake,
    fingerprint,
    receipt_digest,
    wire_bytes,
)


class JobConflict(ValueError):
    """A key/revision/state conflicts with an existing operation."""


class JobRecordError(ValueError):
    def __init__(self, job_id: str):
        super().__init__("Persisted job record failed validation")
        self.job_id = job_id


class ExecutionRecord(StrictModel):
    identity: ExecutionIdentity
    deadline: float
    consumed: bool = False
    receipts: list[Receipt] = Field(default_factory=list, max_length=4)
    conflicts: list[dict] = Field(default_factory=list, max_length=8)
    quarantined: bool = False
    retired: bool = False
    resolution: EvidenceFile | None = None
    retirement: EvidenceFile | None = None


class JobRecord(StrictModel):
    record_version: Literal[1, 2] = 1
    record_revision: int = Field(default=0, ge=0)
    job_id: Identifier
    state: JobState
    phase: ShortText
    request: dict
    fingerprint: Hash
    created_at: float
    updated_at: float
    result: dict | None
    error: str | None
    execution: ExecutionRecord | None = None

    @field_validator("request", mode="before")
    @classmethod
    def independent_request(cls, value):
        wire_bytes(value)
        return value


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class JobStore:
    """Never steals a native lease: an unknown write requires reconciliation."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.records = self.root / "jobs"
        self.keys = self.root / "keys"
        self.records.mkdir(exist_ok=True)
        self.keys.mkdir(exist_ok=True)

    @contextmanager
    def _guard(self):
        path = self.root / ".metadata.lock"
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        locked = False
        try:
            # Keep the inode and use an OS-held lock, which is released on a crash.
            # The separate native.lock is durable and is never automatically stolen.
            deadline = time.monotonic() + 3
            while True:
                try:
                    os.lseek(fd, 0, os.SEEK_SET)
                    if os.name == "nt":
                        import msvcrt

                        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                    break
                except OSError as exc:
                    if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                        raise
                    if time.monotonic() >= deadline:
                        raise JobConflict("Job metadata is busy; no write was repeated") from None
                    time.sleep(0.02)
            yield
        finally:
            if locked:
                os.lseek(fd, 0, os.SEEK_SET)
                if os.name == "nt":
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def _path(self, job_id: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{32}", job_id):
            raise ValueError("Invalid job identifier")
        return self.records / f"{job_id}.json"

    def read(self, job_id: str) -> dict:
        path = self._path(job_id)
        try:
            record = JobRecord.model_validate_json(path.read_text(encoding="utf-8"))
            if record.job_id != job_id or fingerprint(record.request) != record.fingerprint:
                raise JobRecordError(job_id)
            if record.execution:
                identity = record.execution.identity
                if identity.job_id != job_id or identity.request_fingerprint != record.fingerprint:
                    raise JobRecordError(job_id)
            return record.model_dump()
        except (ValidationError, json.JSONDecodeError) as exc:
            raise JobRecordError(job_id) from exc

    def submit(self, idempotency_key: str, request: dict) -> dict:
        if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 160:
            raise ValueError("An idempotency key of 1..160 characters is required")
        request_fingerprint = fingerprint(request)
        request = json.loads(wire_bytes(request))
        key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
        key_path = self.keys / f"{key_hash}.json"
        with self._guard():
            if key_path.exists():
                key = json.loads(key_path.read_text(encoding="utf-8"))
                if key["fingerprint"] != request_fingerprint:
                    raise JobConflict("Idempotency key was already used with different arguments")
                return self.read(key["job_id"])
            now = time.time()
            job = {
                "record_version": 2,
                "record_revision": 0,
                "job_id": uuid.uuid4().hex,
                "state": "queued",
                "phase": "queued",
                "request": request,
                "fingerprint": request_fingerprint,
                "created_at": now,
                "updated_at": now,
                "result": None,
                "error": None,
                "execution": None,
            }
            # A crash between record and key publication leaves an unclaimed orphan;
            # workers only execute a job explicitly returned by submit, never scan it.
            atomic_json(self._path(job["job_id"]), job)
            atomic_json(key_path, {"job_id": job["job_id"], "fingerprint": request_fingerprint})
            return job

    def _save(self, job: dict) -> dict:
        job.update(
            record_version=2, record_revision=job["record_revision"] + 1, updated_at=time.time()
        )
        value = JobRecord.model_validate(job).model_dump()
        atomic_json(self._path(job["job_id"]), value)
        return value

    def _lease(self) -> ExecutionIdentity | None:
        path = self.root / "native.lock"
        if not path.exists():
            return None
        try:
            return ExecutionIdentity.model_validate_json(path.read_text(encoding="utf-8"))
        except (ValidationError, ValueError) as exc:
            raise JobConflict("Legacy or invalid native lease requires isolated review") from exc

    def _release(self, identity: ExecutionIdentity) -> None:
        lease = self._lease()
        if lease == identity:
            (self.root / "native.lock").unlink()

    def _identity_job(self, identity: ExecutionIdentity) -> dict:
        identity = ExecutionIdentity.model_validate(identity.model_dump())
        job = self.read(identity.job_id)
        if not job["execution"] or job["execution"]["identity"] != identity.model_dump():
            raise JobConflict("Attempt identity does not match the durable job")
        return job

    def _admission_blocked(self, session_id: str, *, prepared_job: str | None = None) -> bool:
        # The job is authoritative for past effects, independently of native.lock.
        # Never execute records found by scanning, or repair a lease based on age/PID.
        for path in self.records.glob("*.json"):
            job = self.read(path.stem)
            execution = job["execution"]
            if job["state"] in {"running", "cancel_requested"} and job["job_id"] != prepared_job:
                return True
            if job["state"] in {"outcome_unknown", "interrupted"}:
                return True
            if execution and execution["quarantined"]:
                if execution["conflicts"] or not execution["retired"]:
                    return True
                if execution["identity"]["executor_session_id"] == session_id:
                    return True
        return False

    def prepare_job(
        self,
        job_id: str,
        *,
        profile: BuildProfile,
        handshake: ExecutorHandshake,
        deadline: float,
    ) -> Dispatch:
        with self._guard():
            job = self.read(job_id)
            request = job["request"]
            admit_fake(profile, handshake, request.get("operation", ""))
            if job["state"] != "queued" or job["execution"]:
                raise JobConflict("Only an unprepared queued job may be prepared")
            if self._admission_blocked(handshake.executor_session_id):
                raise JobConflict("Unresolved effects or an unsafe executor block new dispatch")
            identity = ExecutionIdentity(
                job_id=job_id,
                request_fingerprint=job["fingerprint"],
                attempt_id=uuid.uuid4().hex,
                executor_session_id=handshake.executor_session_id,
                process_instance_id=handshake.process_instance_id,
                fencing_token=uuid.uuid4().hex,
                build_profile_id=profile.profile_id,
                build_fingerprint=profile.build_fingerprint,
                isolation_id=handshake.isolation_id,
                operation=request.get("operation"),
                document_id=request.get("document_id"),
                expected_revision=request.get("expected_revision"),
            )
            dispatch = Dispatch(identity=identity, request=request, deadline=deadline)
            if dispatch.deadline <= time.time():
                raise JobConflict("Deadline expired before preparation; nothing dispatched")
            lock_path = self.root / "native.lock"
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                raise JobConflict("An existing native lease must not be stolen") from None
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(identity.model_dump(), stream, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            # A crash before this publication leaves a lease with a queued job.
            # That state is deliberately blocked, never treated as an executable orphan.
            job.update(
                state="running",
                phase="prepared",
                execution=ExecutionRecord(identity=identity, deadline=deadline).model_dump(),
            )
            self._save(job)
            return dispatch

    def dispatch_once(
        self,
        dispatch: Dispatch,
        *,
        profile: BuildProfile,
        handshake: ExecutorHandshake,
        observed_revision: int,
    ) -> bool:
        if type(observed_revision) is not int or observed_revision < 1:
            raise ValueError("Observed revision must be a positive integer")
        dispatch = Dispatch.model_validate(dispatch.model_dump())
        identity = dispatch.identity
        admit_fake(profile, handshake, identity.operation)
        for field in (
            "executor_session_id",
            "process_instance_id",
            "build_profile_id",
            "build_fingerprint",
            "isolation_id",
        ):
            if getattr(handshake, field) != getattr(identity, field):
                raise JobConflict("Executor handshake changed before dispatch")
        with self._guard():
            job = self._identity_job(identity)
            execution = job["execution"]
            if fingerprint(dispatch.request) != job["fingerprint"]:
                raise JobConflict("Payload changed before dispatch")
            if dispatch.deadline != execution["deadline"]:
                raise JobConflict("Dispatch deadline changed")
            if execution["consumed"]:
                return False
            if not execution["quarantined"] and (job["state"], job["phase"]) in {
                ("cancelled", "cancelled_before_execution"),
                ("failed", "native_not_dispatched"),
            }:
                # Repair only the confirmed no-effect publication/unlink window.
                self._release(identity)
                return False
            if self._admission_blocked(identity.executor_session_id, prepared_job=identity.job_id):
                raise JobConflict("Quarantine blocks prepared dispatch")
            if self._lease() != identity or job["state"] not in {"running", "cancel_requested"}:
                raise JobConflict("Dispatch does not own a live prepared lease")
            if job["state"] == "cancel_requested":
                job.update(state="cancelled", phase="cancelled_before_execution")
                self._save(job)
                self._release(identity)
                return False
            if observed_revision != identity.expected_revision or dispatch.deadline <= time.time():
                job.update(
                    state="failed",
                    phase="native_not_dispatched",
                    error="Stale revision or deadline",
                )
                self._save(job)
                self._release(identity)
                return False
            execution["consumed"] = True
            job["phase"] = "invoke_intent_recorded"
            self._save(job)
            # The receiver may invoke its fake operation only after this durable commit.
            # Failure after it is not a licence to retry, even if no effect occurred.
            return True

    def _unknown(self, job: dict, reason: str) -> dict:
        job.update(state="outcome_unknown", phase="reconciliation_required", error=reason[:1000])
        if job["execution"]:
            job["execution"]["quarantined"] = True
        return self._save(job)

    def mark_unknown(self, identity: ExecutionIdentity, reason: str) -> dict:
        if type(reason) is not str:
            raise ValueError("Unknown reason must be plain text")
        with self._guard():
            job = self._identity_job(identity)
            if job["state"] == "outcome_unknown":
                return job
            if job["state"] not in {"running", "cancel_requested"} or self._lease() != identity:
                raise JobConflict("Only an owned active attempt may become unknown")
            return self._unknown(job, reason)

    def record_receipt(self, receipt: Receipt) -> dict:
        receipt = Receipt.model_validate(receipt.model_dump())
        wire_bytes(receipt.model_dump())
        with self._guard():
            job = self.read(receipt.identity.job_id)
            execution = job["execution"]
            if not execution:
                raise JobConflict("Legacy records cannot acquire fabricated execution evidence")
            value = receipt.model_dump()
            receipts = execution["receipts"]
            if any(wire_bytes(value) == wire_bytes(previous) for previous in receipts):
                return job
            valid = (
                value["identity"] == execution["identity"]
                and execution["consumed"]
                and receipt.sequence == len(receipts) + 1
                and receipt.phase == PHASES[receipt.sequence - 1]
                and job["state"] in {"running", "cancel_requested", "outcome_unknown"}
            )
            if receipt.sequence == 4 and receipt.outcome == "succeeded":
                valid = valid and not any(r["outcome"] == "failed" for r in receipts)
            if not valid:
                if len(execution["conflicts"]) < 8:
                    execution["conflicts"].append(value)
                execution["quarantined"] = True
                if job["state"] in {"running", "cancel_requested", "outcome_unknown"}:
                    self._unknown(job, "Conflicting or out-of-order execution receipt")
                else:
                    self._save(job)
                raise JobConflict("Conflicting receipt retained; execution remains quarantined")
            receipts.append(value)
            if job["state"] != "outcome_unknown":
                job["phase"] = receipt.phase
            return self._save(job)

    def _completion(self, job: dict) -> dict:
        execution = job["execution"]
        if not execution or execution["conflicts"] or not execution["consumed"]:
            raise JobConflict("A clean consumed attempt is required")
        receipts = execution["receipts"]
        if len(receipts) != 4:
            raise JobConflict("Return, observation, release and post-scope evidence are required")
        for index, receipt in enumerate(receipts):
            if (
                receipt["sequence"] != index + 1
                or receipt["phase"] != PHASES[index]
                or receipt["identity"] != execution["identity"]
            ):
                raise JobConflict("Execution evidence chain is inconsistent")
        final = receipts[-1]
        if final["outcome"] == "succeeded" and any(r["outcome"] == "failed" for r in receipts):
            raise JobConflict("An earlier failure cannot be overwritten by final success")
        if any(r["cleanup"] == "failed" for r in receipts):
            raise JobConflict("Failed cleanup requires separate evidence and review")
        if final["effects"] == "unknown" or final["cleanup"] != "complete":
            raise JobConflict("Unknown effects or incomplete cleanup cannot complete normally")
        return final

    def complete(self, identity: ExecutionIdentity) -> dict:
        with self._guard():
            job = self._identity_job(identity)
            if job["state"] == "outcome_unknown" or job["execution"]["quarantined"]:
                raise JobConflict("Unknown or quarantined attempts require verified reconciliation")
            final = self._completion(job)
            if job["state"] in {"succeeded", "failed"}:
                # Repair only the known publication/unlink crash window, never execute again.
                if job["state"] != final["outcome"] or wire_bytes(job["result"]) != wire_bytes(
                    final["result"]
                ):
                    raise JobConflict("Terminal result conflicts with completion evidence")
                self._release(identity)
                return job
            if job["state"] not in {"running", "cancel_requested"} or self._lease() != identity:
                raise JobConflict("Completion does not own the active lease")
            job.update(
                state=final["outcome"],
                phase="completed",
                result=final["result"],
                error=None,
            )
            job = self._save(job)
            self._release(identity)
            return job

    def _witness(self, identity: ExecutionIdentity, evidence: EvidenceFile, kind: str) -> dict:
        value = evidence.read_verified(self.root / "evidence")
        if (
            wire_bytes(value.get("identity")) != wire_bytes(identity.model_dump())
            or value.get("scope") != "portable_fake"
            or value.get("kind") != kind
        ):
            raise JobConflict("Independent fake evidence does not match this attempt")
        return value

    def reconcile_verified(
        self, identity: ExecutionIdentity, *, expected_record_revision: int, evidence: EvidenceFile
    ) -> dict:
        with self._guard():
            job = self._identity_job(identity)
            if (
                job["state"] != "outcome_unknown"
                or job["record_revision"] != expected_record_revision
            ):
                raise JobConflict("Reconciliation requires the current unknown record revision")
            witness = self._witness(identity, evidence, "outcome")
            final = self._completion(job)
            if witness.get("receipt_digest") != receipt_digest(job["execution"]["receipts"]):
                raise JobConflict("Independent evidence does not bind the entire receipt chain")
            job["execution"]["resolution"] = evidence.model_dump()
            job.update(
                state=final["outcome"], phase="reconciled", result=final["result"], error=None
            )
            # Past effects can be known while this executor must still be retired.
            return self._save(job)

    def retire_executor(self, identity: ExecutionIdentity, *, evidence: EvidenceFile) -> dict:
        with self._guard():
            job = self._identity_job(identity)
            if not job["execution"]["quarantined"]:
                raise JobConflict("This retirement path is only for quarantined fake executors")
            witness = self._witness(identity, evidence, "retirement")
            if witness.get("executor_stopped") is not True:
                raise JobConflict("Executor termination was not independently witnessed")
            job["execution"]["retired"] = True
            job["execution"]["retirement"] = evidence.model_dump()
            job = self._save(job)
            self._release(identity)
            return job

    def cancel(self, job_id: str) -> dict:
        with self._guard():
            job = self.read(job_id)
            if job["state"] == "queued":
                lease = self._lease()
                if lease and lease.job_id == job_id:
                    return self._unknown(job, "Preparation was interrupted; lease requires review")
                job.update(state="cancelled", phase="cancelled_before_execution")
            elif job["state"] == "running":
                job.update(state="cancel_requested", phase="waiting_for_safe_boundary")
            return self._save(job)

    @staticmethod
    def outcome_certainty(job: dict) -> str:
        execution = job.get("execution")
        if job["state"] in {"running", "cancel_requested", "interrupted", "outcome_unknown"}:
            return "unknown"
        if execution and execution["conflicts"]:
            return "unknown"
        return "known"
