"""The acceptance harness must fail closed without invoking vendor code."""

import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def harness(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "mnova_adapter" / "native_probe.py"
    spec = importlib.util.spec_from_file_location("native_probe_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "MAILBOX", tmp_path)

    def forbidden():
        pytest.fail("A rejected acceptance request reached the native probe")

    monkeypatch.setattr(module, "probe", forbidden)
    return module, tmp_path


@pytest.mark.parametrize(
    "operation", ["process_1d", "save_verify", "edit_regions", "destroy", "execute"]
)
def test_mutations_rejected_before_native_call_or_receipt(harness, operation):
    module, mailbox = harness
    request = {"schema_version": 1, "request_id": "guard-test", "operation": operation}
    (mailbox / "request.json").write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(ValueError, match="Native mutation disabled"):
        module.main()
    assert {path.name for path in mailbox.iterdir()} == {"request.json"}


@pytest.mark.parametrize("receipt_suffix", ["started", "receipt"])
def test_existing_receipt_prevents_probe_replay(harness, receipt_suffix):
    module, mailbox = harness
    request = {"schema_version": 1, "request_id": "same-id", "operation": "probe"}
    (mailbox / "request.json").write_text(json.dumps(request), encoding="utf-8")
    receipt = mailbox / f"same-id.{receipt_suffix}.json"
    receipt.write_text("{}", encoding="utf-8")
    module.main()
    assert receipt.read_text(encoding="utf-8") == "{}"
    assert len(list(mailbox.iterdir())) == 2
