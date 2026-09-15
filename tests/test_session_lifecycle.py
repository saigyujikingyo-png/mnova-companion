"""Portable safety checks only; vendor doubles do not establish native acceptance."""

import builtins
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.mark.parametrize("ownership_state", ["current", "previous", "absent"])
def test_snapshot_does_not_read_scientific_content_under_old_session_ownership(
    harness, monkeypatch, ownership_state
):
    module, mailbox = harness
    document = SimpleNamespace(
        uuid="reopened-document-with-persisted-uuid",
        currentPage=None,
        pageCount=1,
        pageItems=lambda: [],
        currentPageIndex=0,
        activeItem=None,
        getSelectedPages=lambda: [],
        getSelectedPageItems=lambda: [],
    )
    other = SimpleNamespace(**(vars(document) | {"uuid": "unrelated-document"}))
    plugin = SimpleNamespace(documents=lambda: [document, other])
    framework = SimpleNamespace(activeDocument=document)
    monkeypatch.setitem(
        sys.modules,
        "MnovaDocument",
        SimpleNamespace(DocumentPlugin=SimpleNamespace(instance=plugin)),
    )
    monkeypatch.setitem(
        sys.modules,
        "MnovaFramework",
        SimpleNamespace(Framework=SimpleNamespace(instance=framework)),
    )
    observer = {
        "rows": [{"uuid": doc.uuid, "is_modified": False} for doc in (document, other)],
        "active_uuid": document.uuid,
        "enable_undo": True,
    }
    monkeypatch.setitem(
        sys.modules,
        "MnovaJS",
        SimpleNamespace(
            JSPlugin=SimpleNamespace(
                instance=SimpleNamespace(evaluate=Mock(return_value=json.dumps(observer)))
            )
        ),
    )
    if ownership_state != "absent":
        (mailbox / "ownership.json").write_text(
            json.dumps(
                {
                    "pid": module.os.getpid()
                    if ownership_state == "current"
                    else module.os.getpid() + 1,
                    "sentinel_uuid": document.uuid,
                }
            ),
            encoding="utf-8",
        )
    content_reader = Mock(return_value={"spectra": []})
    monkeypatch.setattr(module, "owned_content", content_reader)
    result = module.snapshot()
    assert "owned_content" not in result["documents"][1]
    if ownership_state == "current":
        content_reader.assert_called_once_with(document)
        assert result["documents"][0]["owned_content"] == {"spectra": []}
    else:
        content_reader.assert_not_called()
        assert "owned_content" not in result["documents"][0]


@pytest.fixture
def harness(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "mnova_adapter" / "session_lifecycle.py"
    spec = importlib.util.spec_from_file_location("session_lifecycle_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "MAILBOX", tmp_path)
    return module, tmp_path


@pytest.fixture
def native_boundary(harness, monkeypatch):
    module, _ = harness
    # Exercise historical guards with isolated doubles; the shipped gate stays closed.
    monkeypatch.setattr(module, "MUTATIONS_ENABLED", True)
    plugin = Mock(spec=["newDocument", "closeDocument", "documents"])
    framework = Mock(spec=["getAction"])
    monkeypatch.setitem(
        sys.modules,
        "MnovaDocument",
        SimpleNamespace(DocumentPlugin=SimpleNamespace(instance=plugin)),
    )
    monkeypatch.setitem(
        sys.modules,
        "MnovaFramework",
        SimpleNamespace(Framework=SimpleNamespace(instance=framework)),
    )
    state = {
        "pid": module.os.getpid(),
        "documents": [
            {
                "uuid": "sentinel",
                "is_modified": False,
                "page_count": 1,
                "item_count": 1,
                "owned_content": {"spectra": [{"points": 16}]},
            }
        ],
        "active_uuid": "sentinel",
        "ui_active_uuid": "sentinel",
        "enable_undo": False,
    }
    observer = Mock(return_value=state)
    monkeypatch.setattr(module, "snapshot", observer)
    return plugin, framework, state, observer


def request_for(operation="inspect", **changes):
    request = {
        "schema_version": 1,
        "request_id": "guard-test",
        "operation": operation,
        "expected_snapshot": None if operation == "inspect" else "0" * 64,
    }
    return request | changes


def save_request(mailbox, request):
    (mailbox / "request.json").write_text(json.dumps(request), encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("entrypoint", ["main", "perform"])
@pytest.mark.parametrize(
    "operation", ["create_sentinel", "dirty_action", "create_target", "close_target"]
)
def test_default_gate_rejects_well_formed_mutations_before_import_or_claim(
    harness, monkeypatch, entrypoint, operation
):
    module, mailbox = harness
    assert module.MUTATIONS_ENABLED is False
    request = request_for(operation)
    save_request(mailbox, request)
    real_import = builtins.__import__
    native_imports = []

    def guarded_import(name, *args, **kwargs):
        if name.startswith("Mnova"):
            native_imports.append(name)
            raise AssertionError("The disabled gate attempted a vendor import")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(RuntimeError, match="native mutations remain disabled"):
        if entrypoint == "main":
            module.main()
        else:
            module.perform(request, Mock())

    assert native_imports == []
    assert {path.name for path in mailbox.iterdir()} == {"request.json"}


def save_ownership(module, mailbox, state, **changes):
    record = {
        "pid": module.os.getpid(),
        "sentinel_uuid": "sentinel",
        "creator_request": "creator",
    } | changes
    module.write_json(mailbox / "ownership.json", record)
    module.write_json(
        mailbox / "creator.receipt.json", {"state": "completed", "result": {"snapshot": state}}
    )
    return record


@pytest.mark.parametrize(
    "payload",
    [
        request_for(**{field: value})
        for field, values in {
            "schema_version": [True, 1.0, "1", 0, 2, None],
            "request_id": [
                None,
                True,
                7,
                {},
                [],
                "",
                "-",
                "../x",
                "a/b",
                "a\\b",
                "a b",
                "a_b",
                "é",
                "a" * 81,
            ],
            "operation": [None, True, [], {}, "", "execute", "destroy", "close_all", "process_1d"],
            "expected_snapshot": ["0" * 64, False, 0, {}],
        }.items()
        for value in values
    ]
    + [request_for() | {"script": "untrusted"}]
    + [
        {key: value for key, value in request_for().items() if key != field}
        for field in request_for()
    ],
)
def test_invalid_requests_never_reach_native_or_create_receipts(harness, monkeypatch, payload):
    module, mailbox = harness
    perform = Mock()
    monkeypatch.setattr(module, "perform", perform)
    save_request(mailbox, payload)

    with pytest.raises(ValueError):
        module.main()

    perform.assert_not_called()
    assert {path.name for path in mailbox.iterdir()} == {"request.json"}


@pytest.mark.parametrize(
    "operation", ["create_sentinel", "dirty_action", "create_target", "close_target"]
)
@pytest.mark.parametrize(
    "expected", [None, True, 0, {}, "", "0" * 63, "0" * 65, "F" * 64, "g" * 64]
)
def test_invalid_mutation_precondition_never_reaches_native(
    harness, monkeypatch, operation, expected
):
    module, mailbox = harness
    perform = Mock()
    monkeypatch.setattr(module, "perform", perform)
    save_request(mailbox, request_for(operation, expected_snapshot=expected))

    with pytest.raises(ValueError, match="exact observed snapshot digest"):
        module.main()

    perform.assert_not_called()
    assert {path.name for path in mailbox.iterdir()} == {"request.json"}


@pytest.mark.parametrize("suffix", ["started", "receipt"])
def test_existing_claim_or_receipt_is_preserved_without_replay(harness, monkeypatch, suffix):
    module, mailbox = harness
    perform = Mock()
    monkeypatch.setattr(module, "perform", perform)
    save_request(mailbox, request_for())
    existing = mailbox / f"guard-test.{suffix}.json"
    existing.write_text("incomplete prior evidence", encoding="utf-8")

    module.main()

    perform.assert_not_called()
    assert existing.read_text(encoding="utf-8") == "incomplete prior evidence"
    assert len(list(mailbox.iterdir())) == 2


def test_claim_is_flushed_and_fsynced_before_perform(harness, monkeypatch):
    module, mailbox = harness
    request = request_for()
    save_request(mailbox, request)
    events = []
    real_fsync = module.os.fsync

    def fsync(fd):
        real_fsync(fd)
        assert read_json(mailbox / "guard-test.started.json")["request"] == request
        events.append("fsync")

    def perform(observed, mark):
        assert observed == request
        assert events == ["fsync"]
        events.append("perform")
        mark("observed", evidence="portable double")
        assert read_json(mailbox / "guard-test.progress.json")["stages"][0]["stage"] == "observed"
        return {"scope": "portable test double"}

    monkeypatch.setattr(module.os, "fsync", fsync)
    monkeypatch.setattr(module, "perform", perform)
    module.main()

    receipt = read_json(mailbox / "guard-test.receipt.json")
    assert events == ["fsync", "perform"]
    assert receipt["request"] == request
    assert receipt["state"] == "completed"
    assert receipt["result"] == {"scope": "portable test double"}
    assert "finished_unix" in receipt


def test_claim_sync_failure_prevents_perform_and_retains_no_replay_claim(harness, monkeypatch):
    module, mailbox = harness
    save_request(mailbox, request_for())
    perform = Mock()
    monkeypatch.setattr(module, "perform", perform)
    monkeypatch.setattr(module.os, "fsync", Mock(side_effect=OSError("sync unavailable")))

    with pytest.raises(OSError, match="sync unavailable"):
        module.main()
    module.main()

    perform.assert_not_called()
    assert (mailbox / "guard-test.started.json").exists()
    assert not (mailbox / "guard-test.receipt.json").exists()


def test_perform_failure_persists_stages_and_bounded_error_without_replay(harness, monkeypatch):
    module, mailbox = harness
    save_request(mailbox, request_for())

    def fail_after_mark(request, mark):
        mark("operation_intent")
        raise RuntimeError("failure-" * 400)

    perform = Mock(side_effect=fail_after_mark)
    monkeypatch.setattr(module, "perform", perform)
    module.main()
    receipt_path = mailbox / "guard-test.receipt.json"
    original = receipt_path.read_bytes()
    receipt = json.loads(original)

    assert receipt["state"] == "failed"
    assert receipt["error_type"] == "RuntimeError"
    assert len(receipt["error"]) == 2000
    assert [stage["stage"] for stage in receipt["stages"]] == ["operation_intent"]
    assert "RuntimeError" in receipt["traceback"]
    assert "finished_unix" in receipt
    module.main()
    perform.assert_called_once()
    assert receipt_path.read_bytes() == original


def test_stale_snapshot_rejects_every_mutation_before_native_calls(harness, native_boundary):
    module, mailbox = harness
    plugin, framework, state, _ = native_boundary
    assert module.digest(state) != "0" * 64
    for operation in ["create_sentinel", "dirty_action", "create_target", "close_target"]:
        mark = Mock()
        with pytest.raises(RuntimeError, match="Session changed"):
            module.perform(request_for(operation), mark)
        assert [call.args[0] for call in mark.call_args_list] == ["before"]
    assert plugin.mock_calls == []
    assert framework.mock_calls == []
    assert list(mailbox.iterdir()) == []


def test_default_gate_preserves_read_only_inspection(harness, native_boundary, monkeypatch):
    module, mailbox = harness
    plugin, framework, state, observer = native_boundary
    monkeypatch.setattr(module, "MUTATIONS_ENABLED", False)
    save_request(mailbox, request_for())

    module.main()

    receipt = read_json(mailbox / "guard-test.receipt.json")
    assert receipt["state"] == "completed"
    assert receipt["result"] == {"snapshot": state, "snapshot_sha256": module.digest(state)}
    observer.assert_called_once()
    assert plugin.mock_calls == []
    assert framework.mock_calls == []
    assert list(mailbox.glob("*.intent.json")) == []


@pytest.mark.parametrize(
    "operation", ["create_sentinel", "dirty_action", "create_target", "close_target"]
)
def test_operation_intent_blocks_replay_with_new_request_id(harness, native_boundary, operation):
    module, mailbox = harness
    plugin, framework, state, _ = native_boundary
    intent = mailbox / f"{operation}.intent.json"
    intent.write_text("partial prior intent", encoding="utf-8")
    request = request_for(operation, request_id="new-id", expected_snapshot=module.digest(state))

    with pytest.raises(RuntimeError, match="already attempted"):
        module.perform(request, Mock())

    assert plugin.mock_calls == []
    assert framework.mock_calls == []
    assert intent.read_text(encoding="utf-8") == "partial prior intent"


def test_native_boundary_failure_keeps_intent_and_blocks_a_different_request_id(
    harness, native_boundary
):
    module, mailbox = harness
    plugin, framework, state, _ = native_boundary
    plugin.newDocument.side_effect = RuntimeError("Native outcome unknown")
    request = request_for("create_sentinel", expected_snapshot=module.digest(state))
    save_request(mailbox, request)
    module.main()

    first_path = mailbox / "guard-test.receipt.json"
    first_bytes = first_path.read_bytes()
    first = json.loads(first_bytes)
    assert first["state"] == "failed"
    assert first["error"] == "Native outcome unknown"
    assert first["stages"][-1]["stage"] == "create_sentinel_intent"
    intent_path = mailbox / "create_sentinel.intent.json"
    intent_bytes = intent_path.read_bytes()
    assert read_json(intent_path)["request_id"] == "guard-test"
    assert not (mailbox / "ownership.json").exists()

    save_request(mailbox, request | {"request_id": "new-request"})
    module.main()

    retry = read_json(mailbox / "new-request.receipt.json")
    assert retry["state"] == "failed"
    assert "already attempted" in retry["error"]
    assert first_path.read_bytes() == first_bytes
    assert intent_path.read_bytes() == intent_bytes
    plugin.newDocument.assert_called_once()
    plugin.closeDocument.assert_not_called()
    assert framework.mock_calls == []


@pytest.mark.parametrize("operation", ["dirty_action", "create_target", "close_target"])
def test_wrong_session_ownership_rejects_before_mutation(harness, native_boundary, operation):
    module, mailbox = harness
    plugin, framework, state, _ = native_boundary
    module.write_json(mailbox / "ownership.json", {"pid": module.os.getpid() + 1})
    request = request_for(operation, expected_snapshot=module.digest(state))

    with pytest.raises(RuntimeError, match="different native session"):
        module.perform(request, Mock())

    assert plugin.mock_calls == []
    assert framework.mock_calls == []
    assert not (mailbox / f"{operation}.intent.json").exists()


@pytest.mark.parametrize("creator_state", ["running", "failed", None])
def test_unfinished_creator_cannot_authorize_later_mutation(
    harness, native_boundary, creator_state
):
    module, mailbox = harness
    plugin, framework, state, _ = native_boundary
    save_ownership(module, mailbox, state)
    module.write_json(mailbox / "creator.receipt.json", {"state": creator_state})

    with pytest.raises(RuntimeError, match="creation did not complete"):
        module.perform(request_for("dirty_action", expected_snapshot=module.digest(state)), Mock())

    assert plugin.mock_calls == []
    assert framework.mock_calls == []
    assert not (mailbox / "dirty_action.intent.json").exists()


@pytest.mark.parametrize("creator_rows", [[], [{"uuid": "other"}], [{"uuid": "sentinel"}] * 2])
def test_completed_creator_must_identify_exactly_one_owned_document(
    harness, native_boundary, creator_rows
):
    module, mailbox = harness
    plugin, framework, state, _ = native_boundary
    save_ownership(module, mailbox, {"documents": creator_rows})

    with pytest.raises(RuntimeError, match="missing or ambiguous"):
        module.perform(request_for("dirty_action", expected_snapshot=module.digest(state)), Mock())

    assert plugin.mock_calls == []
    assert framework.mock_calls == []


@pytest.mark.parametrize("active_field", ["active_uuid", "ui_active_uuid"])
def test_both_observers_must_agree_on_owned_active_document(harness, native_boundary, active_field):
    module, mailbox = harness
    plugin, framework, state, _ = native_boundary
    save_ownership(module, mailbox, state)
    state[active_field] = "unrelated"

    with pytest.raises(RuntimeError, match="Both native observers"):
        module.perform(request_for("dirty_action", expected_snapshot=module.digest(state)), Mock())

    assert plugin.mock_calls == []
    assert framework.mock_calls == []
    assert not (mailbox / "dirty_action.intent.json").exists()


def test_mutation_intent_is_synced_and_recorded_before_trigger(
    harness, native_boundary, monkeypatch
):
    module, mailbox = harness
    plugin, framework, state, observer = native_boundary
    save_ownership(module, mailbox, state)
    after = copy.deepcopy(state)
    after["documents"][0]["is_modified"] = True
    after["documents"][0]["page_count"] += 1
    observer.side_effect = [state, after]
    request = request_for("dirty_action", expected_snapshot=module.digest(state))
    save_request(mailbox, request)
    real_fsync = module.os.fsync
    synced_intent = []

    def fsync(fd):
        real_fsync(fd)
        path = mailbox / "dirty_action.intent.json"
        if path.exists():
            synced_intent.append(read_json(path))

    def trigger():
        assert synced_intent == [{"request_id": "guard-test", "pid": module.os.getpid()}]
        progress = read_json(mailbox / "guard-test.progress.json")
        assert progress["stages"][-1]["stage"] == "dirty_action_intent"

    action = SimpleNamespace(
        enabled=True, text="Create New Page", trigger=Mock(side_effect=trigger)
    )
    framework.getAction.return_value = action
    monkeypatch.setattr(module.os, "fsync", fsync)
    module.main()

    receipt = read_json(mailbox / "guard-test.receipt.json")
    assert receipt["state"] == "completed"
    assert receipt["result"]["acceptance"] == "pending_separate_read_only_invocation"
    assert receipt["result"]["snapshot"] == after
    action.trigger.assert_called_once()
    assert plugin.mock_calls == []


@pytest.mark.parametrize("operation", ["create_sentinel", "create_target"])
@pytest.mark.parametrize(
    ("returned_uuid", "created_ids"),
    [
        ("sentinel", ["sentinel"]),
        ("new", ["new"]),
        ("new", ["sentinel", "new", "unexpected"]),
        ("new", ["sentinel"]),
        ("new", ["sentinel", "new", "new"]),
    ],
)
def test_creation_must_prove_one_new_identity_before_claiming_ownership(
    harness, native_boundary, operation, returned_uuid, created_ids
):
    module, mailbox = harness
    plugin, framework, state, observer = native_boundary
    state["documents"][0]["is_modified"] = True
    original_ownership = None
    if operation == "create_target":
        save_ownership(module, mailbox, state)
        original_ownership = (mailbox / "ownership.json").read_bytes()
    created = copy.deepcopy(state)
    created["documents"] = [{"uuid": uuid} for uuid in created_ids]
    observer.side_effect = [state, created]
    plugin.newDocument.return_value = SimpleNamespace(uuid=returned_uuid)
    request = request_for(operation, expected_snapshot=module.digest(state))

    with pytest.raises(RuntimeError, match="changed.*inventory"):
        module.perform(request, Mock())

    plugin.newDocument.assert_called_once()
    plugin.closeDocument.assert_not_called()
    assert framework.mock_calls == []
    assert (mailbox / f"{operation}.intent.json").exists()
    if original_ownership is None:
        assert not (mailbox / "ownership.json").exists()
    else:
        assert (mailbox / "ownership.json").read_bytes() == original_ownership
