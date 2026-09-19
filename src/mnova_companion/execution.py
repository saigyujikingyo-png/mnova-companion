"""Internal P0 wire contracts. Only portable fake execution is admitted here."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

from pydantic import Field, field_validator

from .contracts import Hash, Identifier, StrictModel

MAX_WIRE_BYTES = 128 * 1024
PHASES = ("native_returned", "observation_completed", "scope_released", "post_scope_verified")


def wire_bytes(value: object) -> bytes:
    """Do not invoke native-object repr, serializers, iteration or conversions."""
    count = 0

    def visit(item, depth):
        nonlocal count
        count += 1
        if depth > 16 or count > 10000:
            raise ValueError("Wire value exceeds structural limits")
        kind = type(item)
        if kind in (str, int, bool, type(None)):
            if kind is str and len(item) > MAX_WIRE_BYTES:
                raise ValueError("Wire string exceeds limit")
            if kind is int and not -(2**63) <= item < 2**63:
                raise ValueError("Wire integer exceeds limit")
        elif kind is float:
            if not math.isfinite(item):
                raise ValueError("Wire numbers must be finite")
        elif kind is list:
            for child in item:
                visit(child, depth + 1)
        elif kind is dict:
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError("Wire keys must be strings")
                visit(key, depth + 1)
                visit(child, depth + 1)
        else:
            raise ValueError("Only independent JSON values may cross the execution boundary")

    visit(value, 0)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if len(raw) > MAX_WIRE_BYTES:
        raise ValueError("Wire message exceeds byte limit")
    return raw


def fingerprint(value: object) -> str:
    return hashlib.sha256(wire_bytes(value)).hexdigest()


def receipt_digest(receipts: list[dict]) -> str:
    """Digest bounded messages separately; their chain is not one wire packet."""
    if len(receipts) > 4:
        raise ValueError("Too many phase receipts")
    return fingerprint([fingerprint(receipt) for receipt in receipts])


class BuildProfile(StrictModel):
    profile_id: Identifier
    build_fingerprint: Hash
    mode: Literal["portable_fake", "diagnostic_candidate", "native_accepted"]
    operations: Annotated[list[Identifier], Field(min_length=1, max_length=16)]
    observer_level: Annotated[int, Field(ge=0, le=4)] = 0


class ExecutorHandshake(StrictModel):
    executor_session_id: Identifier
    process_instance_id: Identifier
    build_profile_id: Identifier
    build_fingerprint: Hash
    isolation_id: Identifier
    mode: Literal["portable_fake", "diagnostic_candidate", "native_accepted"]


class ExecutionIdentity(StrictModel):
    job_id: Identifier
    request_fingerprint: Hash
    attempt_id: Identifier
    executor_session_id: Identifier
    process_instance_id: Identifier
    fencing_token: Identifier
    build_profile_id: Identifier
    build_fingerprint: Hash
    isolation_id: Identifier
    operation: Identifier
    document_id: Identifier
    expected_revision: Annotated[int, Field(ge=1)]
    evidence_scope: Literal["portable_fake"] = "portable_fake"


class Dispatch(StrictModel):
    identity: ExecutionIdentity
    request: dict
    deadline: Annotated[float, Field(gt=0)]

    @field_validator("request", mode="before")
    @classmethod
    def independent_values(cls, value):
        wire_bytes(value)
        return value


class Receipt(StrictModel):
    identity: ExecutionIdentity
    sequence: Annotated[int, Field(ge=1, le=4)]
    phase: Literal[
        "native_returned", "observation_completed", "scope_released", "post_scope_verified"
    ]
    effects: Literal["unknown", "none", "known"] = "unknown"
    cleanup: Literal["unknown", "complete", "failed"] = "unknown"
    outcome: Literal["succeeded", "failed"] = "succeeded"
    result: dict = Field(default_factory=dict)

    @field_validator("result", mode="before")
    @classmethod
    def independent_values(cls, value):
        wire_bytes(value)
        return value


class EvidenceFile(StrictModel):
    """A bounded, materialized witness under the store's evidence directory."""

    relative_path: Annotated[str, Field(min_length=1, max_length=240)]
    size_bytes: Annotated[int, Field(ge=1, le=MAX_WIRE_BYTES)]
    sha256: Hash

    @field_validator("relative_path")
    @classmethod
    def local_relative_path(cls, value):
        path = PurePosixPath(value)
        if path.is_absolute() or any(p in {"..", "."} for p in value.split("/")):
            raise ValueError("Evidence path must stay inside its directory")
        if any(c in value for c in "\\:\0") or "//" in value:
            raise ValueError("Evidence path is not a portable relative path")
        return value

    def read_verified(self, directory: Path) -> dict:
        root = directory.resolve(strict=True)
        path = (root / self.relative_path).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("Evidence is outside its directory")
        with path.open("rb") as stream:
            raw = stream.read(MAX_WIRE_BYTES + 1)
        if len(raw) != self.size_bytes or hashlib.sha256(raw).hexdigest() != self.sha256:
            raise ValueError("Evidence integrity mismatch")
        value = json.loads(raw)
        wire_bytes(value)
        if type(value) is not dict:
            raise ValueError("Evidence must be an object")
        return value


def admit_fake(profile: BuildProfile, handshake: ExecutorHandshake, operation: str) -> None:
    """Native/diagnostic profiles are representable, but never enabled by P0."""
    profile = BuildProfile.model_validate(profile.model_dump())
    handshake = ExecutorHandshake.model_validate(handshake.model_dump())
    if (
        profile.mode != "portable_fake"
        or handshake.mode != "portable_fake"
        or handshake.build_profile_id != profile.profile_id
        or handshake.build_fingerprint != profile.build_fingerprint
        or operation not in profile.operations
    ):
        raise ValueError("P0 permits only a matching portable fake profile and handshake")
