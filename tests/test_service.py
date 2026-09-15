import base64
import json

from jsonschema import Draft202012Validator

from mnova_companion.contracts import OUTPUTS
from mnova_companion.service import Service


def checked(service, name, args):
    result = service.call(name, args)
    payload = result.structured_content
    Draft202012Validator(OUTPUTS[name].model_json_schema()).validate(payload)
    assert json.loads(result.content[0].text) == payload
    assert result.is_error == (payload["error"] is not None)
    return result


def test_stage_is_explicit_and_requires_selected_input_root(tmp_path):
    source = tmp_path / "inputs"
    source.mkdir()
    raw = source / "fid"
    raw.write_bytes(b"synthetic raw bytes")
    service = Service(tmp_path / "state")
    assert checked(service, "mnova_open", {"source": str(source)}).is_error
    service = Service(tmp_path / "state", allowed_input_roots=[source])
    result = checked(service, "mnova_open", {"source": str(source)})
    assert result.structured_content["data"]["native_import_state"] == "not_run"
    assert result.structured_content["evidence_scope"] == ["file_staging_only"]
    assert raw.read_bytes() == b"synthetic raw bytes"


def test_unverified_native_write_never_creates_job(tmp_path):
    service = Service(tmp_path)
    result = checked(service, "mnova_run", {"operation": "process_1d", "idempotency_key": "once"})
    assert result.is_error
    assert result.structured_content["error"]["code"] == "CAPABILITY_UNVERIFIED"
    assert list(service.jobs.records.iterdir()) == []


def test_native_bytes_are_content_and_delivery_is_not_overclaimed(tmp_path):
    service = Service(tmp_path)
    native = service.artifacts.root / "sample.mnova"
    native.write_bytes(b"synthetic non-native test bytes")
    meta = service.artifacts.register(native, "j1", "native_test_fixture")
    result = checked(
        service, "mnova_artifacts", {"action": "read", "artifact_id": meta["artifact_id"]}
    )
    assert base64.b64decode(result.content[1].resource.blob) == native.read_bytes()
    assert "blob" not in json.dumps(result.structured_content)
    assert not result.structured_content["data"]["destination_verified"]
    native.write_bytes(b"changed")
    result = checked(
        service, "mnova_artifacts", {"action": "read", "artifact_id": meta["artifact_id"]}
    )
    assert result.is_error


def test_invalid_arguments_and_malformed_output_are_distinct(tmp_path, monkeypatch):
    service = Service(tmp_path)
    invalid = checked(service, "mnova_status", {"surprise": True})
    assert invalid.structured_content["error"]["code"] == "INVALID_ARGUMENT"
    monkeypatch.setattr(service.artifacts, "list_artifacts", lambda _: [{"artifact_id": "bad"}])
    malformed = checked(service, "mnova_artifacts", {})
    assert malformed.structured_content["error"]["code"] == "OUTPUT_CONTRACT_INVALID"


def test_help_contracts_and_unknown_job(tmp_path):
    service = Service(tmp_path)
    help_result = checked(service, "mnova_help", {"operation": "mnova_run"})
    operation = help_result.structured_content["data"]["operations"][0]
    assert not operation["implemented"]
    assert json.loads(operation["output_schema_json"])["type"] == "object"
    unknown = checked(service, "mnova_job", {"job_id": "0" * 32})
    assert unknown.structured_content["error"]["code"] == "NOT_FOUND"


def test_failed_job_can_be_successfully_queried(tmp_path):
    service = Service(tmp_path)
    job = service.jobs.submit("test", {"operation": "probe"})
    assert service.jobs.claim(job["job_id"])
    service.jobs.complete(job["job_id"], {"native_outcome": "failed"}, failed=True)
    result = checked(service, "mnova_job", {"job_id": job["job_id"]})
    assert not result.is_error
    assert result.structured_content["data"]["state"] == "failed"


def test_corrupt_job_returns_structured_error_with_known_job(tmp_path):
    service = Service(tmp_path)
    job = service.jobs.submit("corrupt", {"operation": "probe"})
    path = service.jobs.records / f"{job['job_id']}.json"
    record = json.loads(path.read_text())
    del record["phase"]
    path.write_text(json.dumps(record))
    result = checked(service, "mnova_job", {"job_id": job["job_id"]})
    assert result.structured_content["error"]["code"] == "OUTPUT_CONTRACT_INVALID"
    assert result.structured_content["error"]["job_id"] == job["job_id"]
