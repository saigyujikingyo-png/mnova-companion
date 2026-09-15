"""Versioned public contracts. Unavailable evidence never becomes success."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ShortText = Annotated[str, Field(min_length=1, max_length=240)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
JobState = Literal[
    "queued",
    "running",
    "awaiting_user",
    "succeeded",
    "partially_succeeded",
    "failed",
    "cancel_requested",
    "cancelled",
    "interrupted",
    "outcome_unknown",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Error(StrictModel):
    code: Literal[
        "INVALID_ARGUMENT",
        "NOT_FOUND",
        "MODULE_UNAVAILABLE",
        "CAPABILITY_UNVERIFIED",
        "DOCUMENT_CONFLICT",
        "NATIVE_TIMEOUT",
        "OUTCOME_UNKNOWN",
        "OUTPUT_CONTRACT_INVALID",
        "NATIVE_REOPEN_FAILED",
        "DELIVERY_FAILED",
        "INTEGRITY_FAILED",
        "BUSY",
    ]
    message: Annotated[str, Field(min_length=1, max_length=1000)]
    recovery: Annotated[str, Field(min_length=1, max_length=1000)]
    retryable: bool = False
    job_id: Identifier | None = None


class Output[Payload: StrictModel](StrictModel):
    contract_version: Literal["1.0"] = "1.0"
    operation: Identifier
    request_id: Identifier
    observed_at: Annotated[str, Field(max_length=40)]
    request_status: Literal["ok", "accepted", "invalid", "error"]
    summary: Annotated[str, Field(max_length=1000)]
    evidence_scope: Annotated[list[ShortText], Field(min_length=1, max_length=8)]
    data: Payload | None = None
    error: Error | None = None

    @model_validator(mode="after")
    def consistent_status(self):
        failed = self.request_status in {"invalid", "error"}
        if failed != (self.error is not None):
            raise ValueError("Error presence must match request status")
        if not failed and self.data is None:
            raise ValueError("Successful results require a typed payload")
        return self


class Capability(StrictModel):
    operation: Identifier
    implemented: bool
    native_verified: bool
    detail: ShortText


class StatusData(StrictModel):
    plugin_version: ShortText
    installation_present: bool
    executable_present: bool
    registered_version: ShortText | None
    executable_version: ShortText | None
    version_source: Literal["registry", "file_metadata", "registry_and_file", "unavailable"]
    license_state: Literal["unknown", "observed_available", "observed_unavailable"]
    native_state: Literal["unverified", "ready", "busy", "unavailable"]
    native_receipt_observed_at: Annotated[str, Field(max_length=40)] | None = None
    capabilities: Annotated[list[Capability], Field(max_length=30)]


class OperationInfo(StrictModel):
    name: Identifier
    description: ShortText
    implemented: bool
    input_schema_json: Annotated[str, Field(max_length=100000)] | None = None
    output_schema_json: Annotated[str, Field(max_length=100000)] | None = None


class HelpData(StrictModel):
    operations: Annotated[list[OperationInfo], Field(max_length=30)]
    next_cursor: Identifier | None = None


class SourceFile(StrictModel):
    path: Annotated[str, Field(min_length=1, max_length=1024)]
    size_bytes: Annotated[int, Field(ge=0)]
    sha256: Hash


class OpenData(StrictModel):
    source_id: Identifier
    files: Annotated[list[SourceFile], Field(max_length=1000)]
    total_bytes: Annotated[int, Field(ge=0)]
    manifest_sha256: Hash
    native_import_state: Literal["not_run", "imported", "failed"]
    document_id: Identifier | None = None
    revision: Annotated[int, Field(ge=1)] | None = None


class RunData(StrictModel):
    job_id: Identifier
    state: JobState
    phase: ShortText
    result_schema_id: ShortText | None = None
    result_ref: Annotated[str, Field(max_length=240)] | None = None
    native_verification: Literal["not_run", "passed", "failed", "unknown"] = "not_run"
    delivery: Literal["not_requested", "pending", "received", "failed"] = "not_requested"


class JobData(RunData):
    cancellation: Literal["before_execution", "requested", "not_supported", "not_requested"]
    outcome_certainty: Literal["known", "unknown"]


class Artifact(StrictModel):
    artifact_id: Identifier
    file_name: Annotated[str, Field(min_length=1, max_length=1024)]
    size_bytes: Annotated[int, Field(ge=0)]
    sha256: Hash
    media_type: Annotated[str, Field(max_length=120)]
    job_id: Identifier
    role: ShortText


class ArtifactData(StrictModel):
    artifacts: Annotated[list[Artifact], Field(max_length=50)]
    content_delivery: Literal["metadata_only", "embedded_resource", "image", "local_copy"]
    destination_verified: bool = False
    next_cursor: Identifier | None = None


class Quantity(StrictModel):
    value: float | None
    unit: ShortText
    availability: Literal["available", "unavailable", "unsupported", "not_calculated"]
    reason: ShortText | None = None

    @model_validator(mode="after")
    def known_value(self):
        available = self.availability == "available"
        if available != (self.value is not None):
            raise ValueError("Quantity availability must agree with its value")
        if not available and not self.reason:
            raise ValueError("Unavailable quantities require a reason")
        return self


OUTPUTS = {
    "mnova_status": Output[StatusData],
    "mnova_help": Output[HelpData],
    "mnova_open": Output[OpenData],
    "mnova_run": Output[RunData],
    "mnova_job": Output[JobData],
    "mnova_artifacts": Output[ArtifactData],
}


class StatusInput(StrictModel):
    pass


class HelpInput(StrictModel):
    operation: Identifier | None = None


class OpenInput(StrictModel):
    source: Annotated[str, Field(min_length=1, max_length=4096)]


class RunInput(StrictModel):
    operation: Literal["probe", "process_1d", "save_verify", "edit_regions"]
    source_id: Identifier | None = None
    document_id: Identifier | None = None
    expected_revision: Annotated[int, Field(ge=1)] | None = None
    idempotency_key: Annotated[str, Field(min_length=1, max_length=160)]


class JobInput(StrictModel):
    job_id: Identifier
    action: Literal["read", "cancel", "reconcile"] = "read"


class ArtifactInput(StrictModel):
    action: Literal["list", "read", "preview"] = "list"
    artifact_id: Identifier | None = None
    job_id: Identifier | None = None
    cursor: Annotated[str, Field(pattern=r"^[0-9]{1,8}$")] | None = None


INPUTS = {
    "mnova_status": StatusInput,
    "mnova_help": HelpInput,
    "mnova_open": OpenInput,
    "mnova_run": RunInput,
    "mnova_job": JobInput,
    "mnova_artifacts": ArtifactInput,
}
