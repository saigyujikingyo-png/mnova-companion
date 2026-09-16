"""The acceptance harness must fail closed without invoking vendor code."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

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


def test_inventory_skips_page_items_attribute_for_zero_pages(harness):
    module, _ = harness

    class ZeroPageDocument:
        uuid = "synthetic-zero-page"
        pageCount = 0

        @property
        def pageItems(self):
            pytest.fail("Zero-page document must not expose pageItems to the probe")

    plugin = SimpleNamespace(documents=lambda: [ZeroPageDocument()])

    inventory = module.document_inventory(plugin)

    assert inventory == [
        {
            "identity_hash": hashlib.sha256(b"synthetic-zero-page").hexdigest(),
            "page_count": 0,
            "page_item_count": None,
            "page_observation": "not_run_no_pages",
        }
    ]
    assert json.loads(json.dumps(inventory))[0]["page_item_count"] is None


@pytest.mark.parametrize("items", [[], [object(), object()]])
def test_inventory_preserves_nonzero_page_output_and_reads_count_first(harness, items):
    module, _ = harness
    observations = []

    class PagedDocument:
        uuid = "synthetic-paged"

        @property
        def pageCount(self):
            observations.append("page_count")
            return 1

        @property
        def pageItems(self):
            assert observations == ["page_count"]
            observations.append("page_items")
            return lambda: items

    plugin = SimpleNamespace(documents=lambda: [PagedDocument()])

    assert module.document_inventory(plugin) == [
        {
            "identity_hash": hashlib.sha256(b"synthetic-paged").hexdigest(),
            "page_count": 1,
            "page_item_count": len(items),
        }
    ]
    assert observations == ["page_count", "page_items"]
