"""Process identity and diagnostic replay guards; not native lifecycle tests."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def harness(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "mnova_adapter" / "execution_context.py"
    spec = importlib.util.spec_from_file_location("execution_context_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "MAILBOX", tmp_path)
    return module, tmp_path


def request():
    return {
        "schema_version": 1,
        "request_id": "context-1",
        "pid": 42,
        "process_created_filetime": 1234,
        "window_handle": 111,
    }


def observation():
    return {
        "pid": 42,
        "process_created_filetime": 1234,
        "image_name": "MestReNova.exe",
        "script_thread_id": 12,
        "window_thread_id": 12,
        "window_pid": 42,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("pid", True),
        ("window_handle", 0),
        ("process_created_filetime", -1),
        ("schema_version", True),
        ("request_id", "../escape"),
        ("request_id", ""),
    ],
)
def test_bad_binding_rejected_before_os_read(harness, monkeypatch, field, value):
    module, mailbox = harness
    reader = Mock(side_effect=AssertionError("OS access was not authorized"))
    monkeypatch.setattr(module, "read_context", reader)
    (mailbox / "request.json").write_text(json.dumps(request() | {field: value}), encoding="utf-8")
    with pytest.raises(ValueError):
        module.main()
    reader.assert_not_called()
    assert len(list(mailbox.iterdir())) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("pid", 43),
        ("process_created_filetime", 1235),
        ("window_pid", 43),
        ("image_name", "python.exe"),
    ],
)
def test_stale_process_or_foreign_window_never_accepted(harness, field, value):
    module, _ = harness
    with pytest.raises(RuntimeError, match="does not match"):
        module.verify_context(request(), observation() | {field: value})


def test_thread_mismatch_is_observed_not_reported_as_native_failure(harness):
    module, _ = harness
    result = module.verify_context(request(), observation() | {"script_thread_id": 13})
    assert result["same_thread"] is False
    assert result["native_writes"] == "not_run"


def test_finished_or_failed_observation_not_replayed(harness, monkeypatch):
    module, mailbox = harness
    reader = Mock(return_value=observation())
    monkeypatch.setattr(module, "read_context", reader)
    (mailbox / "request.json").write_text(json.dumps(request()), encoding="utf-8")
    module.main()
    first = (mailbox / "context-1.receipt.json").read_bytes()
    module.main()
    reader.assert_called_once_with(111)
    assert (mailbox / "context-1.receipt.json").read_bytes() == first
    assert json.loads(first)["result"]["same_thread"] is True


def test_failed_os_read_receipt_not_replayed(harness, monkeypatch):
    module, mailbox = harness
    reader = Mock(side_effect=OSError("Synthetic OS metadata read failure"))
    monkeypatch.setattr(module, "read_context", reader)
    (mailbox / "request.json").write_text(json.dumps(request()), encoding="utf-8")

    module.main()

    receipt = json.loads((mailbox / "context-1.receipt.json").read_bytes())
    assert receipt["state"] == "failed"
    assert receipt["error_type"] == "OSError"
    assert "result" not in receipt
    original = {path.name: path.read_bytes() for path in mailbox.iterdir()}

    module.main()

    reader.assert_called_once_with(111)
    assert {path.name: path.read_bytes() for path in mailbox.iterdir()} == original


def test_orphan_started_claim_not_replayed(harness, monkeypatch):
    module, mailbox = harness
    reader = Mock(side_effect=AssertionError("An unfinished claim must not repeat the OS read"))
    monkeypatch.setattr(module, "read_context", reader)
    (mailbox / "request.json").write_text(json.dumps(request()), encoding="utf-8")
    # A process can stop after claiming the request but before flushing valid JSON.
    (mailbox / "context-1.started.json").write_bytes(b'{"started_unix":')
    original = {path.name: path.read_bytes() for path in mailbox.iterdir()}

    module.main()

    reader.assert_not_called()
    assert {path.name: path.read_bytes() for path in mailbox.iterdir()} == original
    assert not (mailbox / "context-1.receipt.json").exists()
