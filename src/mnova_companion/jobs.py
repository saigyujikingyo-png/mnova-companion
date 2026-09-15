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

from pydantic import ValidationError

from .contracts import Hash, Identifier, JobState, ShortText, StrictModel


class JobConflict(ValueError):
    """A key/revision/state conflicts with an existing operation."""


class JobRecordError(ValueError):
    def __init__(self, job_id: str):
        super().__init__("Persisted job record failed validation")
        self.job_id = job_id


class JobRecord(StrictModel):
    job_id: Identifier
    state: JobState
    phase: ShortText
    request: dict
    fingerprint: Hash
    created_at: float
    updated_at: float
    result: dict | None
    error: str | None


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
            if record.job_id != job_id:
                raise JobRecordError(job_id)
            return record.model_dump()
        except (ValidationError, json.JSONDecodeError) as exc:
            raise JobRecordError(job_id) from exc

    def submit(self, idempotency_key: str, request: dict) -> dict:
        if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 160:
            raise ValueError("An idempotency key of 1..160 characters is required")
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False)
        fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
        key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
        key_path = self.keys / f"{key_hash}.json"
        with self._guard():
            if key_path.exists():
                key = json.loads(key_path.read_text(encoding="utf-8"))
                if key["fingerprint"] != fingerprint:
                    raise JobConflict("Idempotency key was already used with different arguments")
                return self.read(key["job_id"])
            now = time.time()
            job = {
                "job_id": uuid.uuid4().hex,
                "state": "queued",
                "phase": "queued",
                "request": request,
                "fingerprint": fingerprint,
                "created_at": now,
                "updated_at": now,
                "result": None,
                "error": None,
            }
            # A crash between record and key publication leaves an unclaimed orphan;
            # workers only execute a job explicitly returned by submit, never scan it.
            atomic_json(self._path(job["job_id"]), job)
            atomic_json(key_path, {"job_id": job["job_id"], "fingerprint": fingerprint})
            return job

    def claim(self, job_id: str) -> bool:
        with self._guard():
            job = self.read(job_id)
            if job["state"] != "queued":
                return False
            lock_path = self.root / "native.lock"
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                return False
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump({"job_id": job_id, "pid": os.getpid(), "created_at": time.time()}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            job.update(state="running", phase="claimed", updated_at=time.time())
            atomic_json(self._path(job_id), job)
            return True

    def _owns_lease(self, job_id: str) -> bool:
        lock = self.root / "native.lock"
        return lock.exists() and json.loads(lock.read_text(encoding="utf-8"))["job_id"] == job_id

    def phase(self, job_id: str, phase: str) -> None:
        if not phase or len(phase) > 100:
            raise ValueError("Invalid phase")
        with self._guard():
            job = self.read(job_id)
            if job["state"] not in {"running", "cancel_requested"} or not self._owns_lease(job_id):
                raise JobConflict("Job does not own the native lease")
            job.update(phase=phase, updated_at=time.time())
            atomic_json(self._path(job_id), job)

    def mark_unknown(self, job_id: str, reason: str) -> dict:
        with self._guard():
            job = self.read(job_id)
            if job["state"] not in {"running", "cancel_requested"} or not self._owns_lease(job_id):
                raise JobConflict("Job does not own a running native lease")
            job.update(
                state="outcome_unknown",
                phase="reconciliation_required",
                updated_at=time.time(),
                error=reason[:1000],
            )
            atomic_json(self._path(job_id), job)
            return job

    def complete(self, job_id: str, result: dict, *, failed: bool = False) -> dict:
        with self._guard():
            job = self.read(job_id)
            if job["state"] not in {"running", "cancel_requested", "outcome_unknown"}:
                raise JobConflict("Cannot overwrite a terminal or unclaimed job")
            if not self._owns_lease(job_id):
                raise JobConflict("Job does not own the native lease")
            job.update(
                state="failed" if failed else "succeeded",
                phase="completed",
                updated_at=time.time(),
                result=result,
                error=None,
            )
            atomic_json(self._path(job_id), job)
            (self.root / "native.lock").unlink()
            return job

    def cancel(self, job_id: str) -> dict:
        with self._guard():
            job = self.read(job_id)
            if job["state"] == "queued":
                job.update(state="cancelled", phase="cancelled_before_execution")
            elif job["state"] == "running":
                job.update(state="cancel_requested", phase="waiting_for_safe_boundary")
            job["updated_at"] = time.time()
            atomic_json(self._path(job_id), job)
            return job
