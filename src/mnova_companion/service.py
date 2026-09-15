"""Portable service layer. Native mutations stay gated until individually accepted."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from mcp_types import (
    BlobResourceContents,
    CallToolResult,
    EmbeddedResource,
    ImageContent,
    TextContent,
)
from pydantic import ValidationError

from . import __version__
from .artifact_store import ArtifactStore
from .contracts import (
    INPUTS,
    OUTPUTS,
    Artifact,
    ArtifactData,
    Capability,
    Error,
    HelpData,
    JobData,
    OpenData,
    OperationInfo,
    StatusData,
)
from .discovery import discover_installation
from .jobs import JobConflict, JobRecordError, JobStore

DESCRIPTIONS = {
    "mnova_status": "Read installation metadata and current implementation/acceptance limits.",
    "mnova_help": "Discover tools and their versioned contracts on demand.",
    "mnova_open": "Stage an authorised selected input; native import is separately reported.",
    "mnova_run": "Request a named native operation; unavailable operations fail before any write.",
    "mnova_job": "Read/cancel/reconcile a known job; unknown native writes are never repeated.",
    "mnova_artifacts": "Read registered artifact metadata, original bytes or a supported preview.",
}


class Service:
    def __init__(self, root: Path, *, allowed_input_roots: list[Path] | None = None):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.artifacts = ArtifactStore(self.root / "artifacts")
        self.jobs = JobStore(self.root / "state")
        self.allowed_input_roots = [Path(p).resolve() for p in (allowed_input_roots or [])]

    def _output(self, tool, request_id, *, data=None, error=None, summary="", scope=None):
        value = OUTPUTS[tool](
            operation=tool,
            request_id=request_id,
            observed_at=datetime.now(UTC).isoformat(),
            request_status="error" if error else "ok",
            summary=summary,
            evidence_scope=scope or ["portable_core_only"],
            data=data,
            error=error,
        )
        # Serialize, then validate that exact data before giving it to the transport.
        payload = value.model_dump(mode="json")
        OUTPUTS[tool].model_validate(payload)
        return CallToolResult(
            content=[TextContent(text=json.dumps(payload, ensure_ascii=False, allow_nan=False))],
            structuredContent=payload,
            isError=error is not None,
        )

    def call(self, tool: str, arguments: dict) -> CallToolResult:
        if tool not in INPUTS:
            raise KeyError(tool)
        request_id = uuid.uuid4().hex
        try:
            args = INPUTS[tool].model_validate(arguments)
        except ValidationError:
            return self._output(
                tool,
                request_id,
                error=Error(
                    code="INVALID_ARGUMENT",
                    message="Arguments do not match this tool's schema",
                    recovery="Read mnova_help for the tool and correct its typed arguments",
                ),
            )
        try:
            return self._call_validated(tool, args, request_id)
        except JobRecordError as exc:
            return self._output(
                tool,
                request_id,
                error=Error(
                    code="OUTPUT_CONTRACT_INVALID",
                    job_id=exc.job_id,
                    message="Persisted job record failed validation",
                    recovery="Inspect this known job without repeating its native operation",
                ),
                scope=["persisted_job_contract_failure"],
            )
        except ValidationError:
            return self._output(
                tool,
                request_id,
                error=Error(
                    code="OUTPUT_CONTRACT_INVALID",
                    message="Backend data failed its output contract",
                    recovery="Inspect the existing result; do not repeat a write for its format",
                ),
                scope=["output_contract_failure"],
            )
        except JobConflict as exc:
            return self._output(
                tool,
                request_id,
                error=Error(
                    code="DOCUMENT_CONFLICT",
                    message=str(exc)[:1000],
                    recovery="Read the existing job; do not repeat a native write",
                ),
            )
        except FileNotFoundError:
            return self._output(
                tool,
                request_id,
                error=Error(
                    code="NOT_FOUND",
                    message="The requested registered object is unavailable",
                    recovery="Check its identifier or select the input again",
                ),
            )
        except (PermissionError, ValueError, OSError):
            return self._output(
                tool,
                request_id,
                error=Error(
                    code="INTEGRITY_FAILED",
                    message="The selected file or operation failed validation",
                    recovery="Check file permissions, integrity and authorised input roots",
                ),
            )

    def _call_validated(self, tool, args, request_id):
        if tool == "mnova_status":
            metadata = discover_installation()
            return self._output(
                tool,
                request_id,
                data=StatusData(
                    plugin_version=__version__,
                    **metadata,
                    license_state="unknown",
                    native_state="unavailable",
                    capabilities=[
                        Capability(
                            operation="stage_source",
                            implemented=True,
                            native_verified=False,
                            detail="Copy and verify selected input bytes only",
                        ),
                        Capability(
                            operation="artifact_read",
                            implemented=True,
                            native_verified=False,
                            detail="Registered files with size and SHA-256 readback",
                        ),
                        Capability(
                            operation="process_1d",
                            implemented=False,
                            native_verified=False,
                            detail="Lifecycle acceptance failed; native writes are disabled",
                        ),
                    ],
                ),
                summary="Development preview; native writes disabled after lifecycle failure",
                scope=["installation_registration", "portable_core"],
            )
        if tool == "mnova_help":
            names = [args.operation] if args.operation else list(INPUTS)
            if any(name not in INPUTS for name in names):
                raise FileNotFoundError("Unknown operation")
            data = HelpData(
                operations=[
                    OperationInfo(
                        name=name,
                        description=DESCRIPTIONS[name],
                        implemented=name != "mnova_run",
                        input_schema_json=json.dumps(INPUTS[name].model_json_schema())
                        if args.operation
                        else None,
                        output_schema_json=json.dumps(OUTPUTS[name].model_json_schema())
                        if args.operation
                        else None,
                    )
                    for name in names
                ]
            )
            return self._output(tool, request_id, data=data, summary="Versioned tool contracts")
        if tool == "mnova_open":
            source = Path(args.source)
            resolved = source.resolve(strict=True)
            if not any(resolved.is_relative_to(root) for root in self.allowed_input_roots):
                raise PermissionError("Input is outside the owner-selected roots")
            manifest = self.artifacts.stage(source)
            return self._output(
                tool,
                request_id,
                data=OpenData(**manifest, native_import_state="not_run"),
                summary="Input copied and verified. Native document import has not run.",
                scope=["file_staging_only"],
            )
        if tool == "mnova_run":
            return self._output(
                tool,
                request_id,
                error=Error(
                    code="CAPABILITY_UNVERIFIED",
                    message="Native writes disabled after a lifecycle acceptance crash",
                    recovery="Use status/help. No native write or job was started by this request",
                ),
                summary="Requested native operation is not enabled",
            )
        if tool == "mnova_job":
            job = self.jobs.read(args.job_id)
            if args.action == "cancel":
                job = self.jobs.cancel(args.job_id)
            # Reconciliation only reads the durable observation in this preview.
            # It does not infer completion from a missing process or clear a lease.
            data = JobData(
                job_id=job["job_id"],
                state=job["state"],
                phase=job["phase"],
                cancellation=(
                    "requested"
                    if job["state"] == "cancel_requested"
                    else "before_execution"
                    if job["state"] == "cancelled"
                    else "not_requested"
                ),
                outcome_certainty="unknown" if job["state"] == "outcome_unknown" else "known",
            )
            return self._output(tool, request_id, data=data, summary="Persisted job observation")
        return self._artifact_call(args, request_id)

    def _artifact_call(self, args, request_id):
        if args.action == "list":
            rows = self.artifacts.list_artifacts(args.job_id)
            offset = int(args.cursor or 0)
            items = [Artifact(**row) for row in rows[offset : offset + 50]]
            data = ArtifactData(
                artifacts=items,
                content_delivery="metadata_only",
                next_cursor=str(offset + 50) if offset + 50 < len(rows) else None,
            )
            return self._output(
                "mnova_artifacts", request_id, data=data, summary="Registered artifact metadata"
            )
        if not args.artifact_id:
            raise ValueError("An artifact ID is required")
        meta = Artifact(**self.artifacts.metadata(args.artifact_id))
        if meta.size_bytes > 16 * 1024 * 1024:
            raise ValueError("This inline delivery route is limited to 16 MiB")
        raw = self.artifacts.read(args.artifact_id)
        if args.action == "preview":
            if meta.media_type not in {"image/png", "image/jpeg"}:
                raise ValueError("No image preview is registered for this artifact")
            content = ImageContent(data=base64.b64encode(raw).decode(), mimeType=meta.media_type)
            delivery = "image"
        else:
            content = EmbeddedResource(
                resource=BlobResourceContents(
                    uri=f"mnova://artifact/{meta.artifact_id}",
                    mimeType=meta.media_type,
                    blob=base64.b64encode(raw).decode(),
                )
            )
            delivery = "embedded_resource"
        result = self._output(
            "mnova_artifacts",
            request_id,
            data=ArtifactData(artifacts=[meta], content_delivery=delivery),
            summary="Original bytes verified; receiving-host acceptance remains separate",
            scope=["source_bytes_verified", "mcp_content_emitted"],
        )
        result.content.append(content)
        return result
