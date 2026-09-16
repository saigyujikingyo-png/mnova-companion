"""Bounded R0/R1 acceptance experiment, never a public MCP dispatch entrypoint.

Run with Mnova's embedded Python. Requests and raw identities stay in .local.
Only Python creates/closes documents. JavaScript is a synchronous read-only
dirty-state observer; no JS wrapper is intentionally retained or accessed later.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import time
import traceback
from pathlib import Path

MAILBOX = Path(__file__).resolve().parents[1] / ".local" / "native" / "session-r1"
OPERATIONS = {"inspect", "create_sentinel", "dirty_action", "create_target", "close_target"}
# Shipped native writes require separate acceptance; changing request IDs is not recovery.
MUTATIONS_ENABLED = False
# R1 close removed the protected sentinel while leaving the requested target present.
# A private bootstrap enabling other writes must not implicitly authorize this route.
TARGET_CLOSE_ENABLED = False


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    os.replace(temporary, path)


def digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def validate_request(request: dict) -> None:
    if set(request) != {"schema_version", "request_id", "operation", "expected_snapshot"}:
        raise ValueError("Unexpected request fields")
    name = request["request_id"]
    if (
        type(request["schema_version"]) is not int
        or request["schema_version"] != 1
        or not isinstance(name, str)
        or not name
        or not name.isascii()
        or not name.replace("-", "").isalnum()
        or len(name) > 80
        or not isinstance(request["operation"], str)
        or request["operation"] not in OPERATIONS
    ):
        raise ValueError("Invalid bounded acceptance request")
    expected = request["expected_snapshot"]
    if request["operation"] == "inspect":
        if expected is not None:
            raise ValueError("Read-only inspection requires no mutation precondition")
    elif (
        not isinstance(expected, str)
        or len(expected) != 64
        or any(c not in "0123456789abcdef" for c in expected)
    ):
        raise ValueError("Mutation requires the exact observed snapshot digest")


def identity(obj) -> str | None:
    return None if obj is None else str(obj.uuid)


def synthetic_xml() -> str:
    return (
        '<mnova-peaks version="1.0"><spectrum><dim><from>0</from><to>10</to>'
        "<frequency>400</frequency><nucleus>H1</nucleus><nPoints>16384</nPoints>"
        "</dim><solvent>Chloroform-d</solvent></spectrum><peakList>"
        "<peak><heigth>1</heigth><dim><shift>2</shift><width>0.02</width></dim></peak>"
        "<peak><heigth>2</heigth><dim><shift>5</shift><width>0.02</width></dim></peak>"
        "</peakList></mnova-peaks>"
    )


def owned_content(doc) -> dict:
    from MnovaNMR import NMRItem

    spectra = []
    for raw_item in doc.pageItems("NMR Spectrum"):
        item = NMRItem(raw_item)
        spectrum = item.activeSpectrum
        coordinate = spectrum.coords[1]
        spectra.append(
            {
                "item_uuid": str(item.uuid),
                "points": int(coordinate.pts),
                "nucleus": str(coordinate.nucleusStr),
                "frequency_mhz": float(coordinate.MHz),
                "real_sha256": hashlib.sha256(memoryview(spectrum.reData()).tobytes()).hexdigest(),
            }
        )
    return {"spectra": spectra}


def snapshot() -> dict:
    from MnovaDocument import DocumentPlugin
    from MnovaFramework import Framework
    from MnovaJS import JSPlugin

    observer = json.loads(
        JSPlugin.instance.evaluate(
            "(function(){var docs=mainWindow.documents(),rows=[];"
            "for(var i=0;i<docs.length;i++){var d=docs[i];"
            "rows.push({uuid:d.uuid,is_modified:d.isModified});}"
            "return JSON.stringify({rows:rows,active_uuid:mainWindow.activeDocument.uuid,"
            "enable_undo:mainWindow.enableUndo});})()"
        )
    )
    dirty = {row["uuid"]: row["is_modified"] for row in observer["rows"]}
    record_path = MAILBOX / "ownership.json"
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {}
    # A reopened document may retain its UUID in a different process. Historical
    # ownership must not authorize scientific-content reads in that new session.
    owned = (
        {record.get("sentinel_uuid"), record.get("target_uuid")}
        if record.get("pid") == os.getpid()
        else set()
    )
    rows = []
    for doc in DocumentPlugin.instance.documents():
        page_count = int(doc.pageCount)
        if page_count == 0:
            # A session document can exist before its first canvas is available.
            # Do not turn an unobserved canvas/item/selection state into zero.
            row = {
                "uuid": str(doc.uuid),
                "page_count": 0,
                "item_count": None,
                "is_modified": dirty[str(doc.uuid)],
                "current_page_uuid": None,
                "current_page_index": None,
                "active_item_uuid": None,
                "selected_page_uuids": None,
                "selected_item_uuids": None,
                "page_observation": "not_run_no_pages",
            }
            if str(doc.uuid) in owned:
                row["owned_content"] = None
            rows.append(row)
            continue
        page = doc.currentPage
        row = {
            "uuid": str(doc.uuid),
            "page_count": page_count,
            "item_count": len(doc.pageItems()),
            "is_modified": dirty[str(doc.uuid)],
            "current_page_uuid": identity(page),
            "current_page_index": int(doc.currentPageIndex),
            "active_item_uuid": identity(doc.activeItem),
            "selected_page_uuids": [identity(p) for p in doc.getSelectedPages()],
            "selected_item_uuids": [identity(i) for i in doc.getSelectedPageItems()],
        }
        if str(doc.uuid) in owned:
            row["owned_content"] = owned_content(doc)
        rows.append(row)
    if (
        set(dirty) != {r["uuid"] for r in rows}
        or len(dirty) != len(rows)
        or len(dirty) != len(observer["rows"])
    ):
        raise RuntimeError("Native observers disagree on inventory")
    return {
        "pid": os.getpid(),
        "documents": rows,
        "active_uuid": identity(Framework.instance.activeDocument),
        "ui_active_uuid": observer["active_uuid"],
        "enable_undo": observer["enable_undo"],
    }


def owned_record() -> dict:
    record = json.loads((MAILBOX / "ownership.json").read_text(encoding="utf-8"))
    if record["pid"] != os.getpid():
        raise RuntimeError("Ownership belongs to a different native session")
    creator = json.loads(
        (MAILBOX / (record["creator_request"] + ".receipt.json")).read_text(encoding="utf-8")
    )
    if creator.get("state") != "completed":
        raise RuntimeError("Sentinel creation did not complete; reconcile without mutation")
    row_for(creator["result"]["snapshot"], record["sentinel_uuid"])
    return record


def require_target_creation(record: dict) -> None:
    """A partial ownership claim cannot authorize a subsequent target close."""
    try:
        creator_id = record["target_creator_request"]
        if (
            not isinstance(creator_id, str)
            or not creator_id
            or len(creator_id) > 80
            or not creator_id.isascii()
            or not creator_id.replace("-", "").isalnum()
        ):
            raise ValueError("Invalid target creator identity")
        receipt = json.loads((MAILBOX / (creator_id + ".receipt.json")).read_text(encoding="utf-8"))
        if not isinstance(receipt, dict) or receipt.get("state") != "completed":
            raise ValueError("Target creator did not complete")
        request = receipt["request"]
        validate_request(request)
        if request["operation"] != "create_target" or request["request_id"] != creator_id:
            raise ValueError("Target creator request does not match")
        state = receipt["result"]["snapshot"]
        if (
            not isinstance(state, dict)
            or type(state.get("pid")) is not int
            or state["pid"] != record["pid"]
            or not isinstance(state.get("documents"), list)
        ):
            raise ValueError("Target creator snapshot is invalid")
        rows = state["documents"]
        if any(
            not isinstance(row, dict) or not isinstance(row.get("uuid"), str) or not row["uuid"]
            for row in rows
        ) or len({row["uuid"] for row in rows}) != len(rows):
            raise ValueError("Target creator inventory is invalid")
        target = row_for(state, record["target_uuid"])
        if (
            type(target.get("page_count")) is not int
            or target["page_count"] != 1
            or type(target.get("item_count")) is not int
            or target["item_count"] != 0
            or target.get("is_modified") is not False
        ):
            raise ValueError("Target creator document observation is invalid")
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        raise RuntimeError(
            "Target creation evidence is missing, incomplete, or inconsistent"
        ) from exc


def row_for(state: dict, uuid: str) -> dict:
    matches = [row for row in state["documents"] if row["uuid"] == uuid]
    if len(matches) != 1:
        raise RuntimeError("Owned document missing or ambiguous")
    return matches[0]


def require_active(state: dict, uuid: str) -> None:
    if state["active_uuid"] != uuid or state["ui_active_uuid"] != uuid:
        raise RuntimeError("Both native observers must identify the owned active document")


def one_new_identity(before: dict, after: dict, uuid: str) -> bool:
    old_ids = {row["uuid"] for row in before["documents"]}
    new_ids = {row["uuid"] for row in after["documents"]}
    return (
        len(old_ids) == len(before["documents"])
        and uuid not in old_ids
        and new_ids == old_ids | {uuid}
        and len(new_ids) == len(after["documents"])
    )


def resolve(plugin, uuid: str):
    matches = [doc for doc in plugin.documents() if str(doc.uuid) == uuid]
    if len(matches) != 1:
        raise RuntimeError("Owned native document missing or ambiguous")
    return matches[0]


def perform(request: dict, mark) -> dict:
    if request["operation"] != "inspect" and not MUTATIONS_ENABLED:
        raise RuntimeError(
            "Native lifecycle acceptance is incomplete; native mutations remain disabled"
        )
    if request["operation"] == "close_target" and not TARGET_CLOSE_ENABLED:
        raise RuntimeError("R1 target close failed; native close remains disabled")
    from MnovaDocument import DocumentPlugin
    from MnovaFramework import Framework

    before = snapshot()
    mark("before", snapshot=before, snapshot_sha256=digest(before))
    operation = request["operation"]
    if operation == "inspect":
        return {"snapshot": before, "snapshot_sha256": digest(before)}
    if digest(before) != request["expected_snapshot"]:
        raise RuntimeError("Session changed since the reviewed precondition")
    # Also prevent replay under a new request ID, including after an unknown outcome.
    intent = MAILBOX / (operation + ".intent.json")
    if intent.exists():
        raise RuntimeError("This mutation was already attempted; inspect without replay")

    def mutation_intent(stage: str, **details) -> None:
        with intent.open("x", encoding="utf-8") as stream:
            json.dump({"request_id": request["request_id"], "pid": os.getpid()}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        mark(stage, **details)

    plugin, framework = DocumentPlugin.instance, Framework.instance
    if operation == "create_sentinel":
        if (MAILBOX / "ownership.json").exists():
            raise RuntimeError("This experiment already owns a sentinel")
        mutation_intent("create_sentinel_intent")
        parent = plugin.newDocument("Mnova Companion R0 sentinel")
        created_uuid = str(parent.uuid)
        created = snapshot()
        mark("sentinel_created", snapshot=created)
        if not one_new_identity(before, created, created_uuid):
            raise RuntimeError("Creation changed the pre-existing document inventory")
        # Claim only a proven new identity; partial work is never replayed.
        record = {
            "pid": os.getpid(),
            "sentinel_uuid": created_uuid,
            "creator_request": request["request_id"],
        }
        write_json(MAILBOX / "ownership.json", record)
        from MnovaNMR import NMRItem

        page = parent.currentPage if parent.pageCount else parent.newPage()
        item = NMRItem(synthetic_xml())
        page.addItem(item)
        item = page = None  # Drop children while the session parent remains live.
    else:
        record = owned_record()
        sentinel_uuid = record["sentinel_uuid"]
        sentinel_before = row_for(before, sentinel_uuid)
        require_active(before, sentinel_uuid)
        if (
            type(sentinel_before.get("page_count")) is not int
            or sentinel_before["page_count"] <= 0
            or not isinstance(sentinel_before.get("owned_content"), dict)
            or not isinstance(sentinel_before["owned_content"].get("spectra"), list)
        ):
            raise RuntimeError("Sentinel content is unobserved; no mutation is permitted")
        if operation == "dirty_action":
            if sentinel_before["is_modified"] is True:
                raise RuntimeError("Sentinel is already dirty; do not replay an edit")
            action = framework.getAction("action_Edit_CreateNewPage")
            if action is None or not action.enabled:
                raise RuntimeError("Documented Create New Page action is unavailable")
            mutation_intent("dirty_action_intent", action_text=str(action.text))
            action.trigger()
        else:
            if sentinel_before["is_modified"] is not True:
                raise RuntimeError("R0 requires an authentic dirty sentinel")
            if not sentinel_before["owned_content"]["spectra"]:
                raise RuntimeError("Sentinel content is missing")
            if operation == "create_target":
                if "target_uuid" in record:
                    raise RuntimeError("This experiment already owns a target")
                record["sentinel_baseline"] = sentinel_before
                mutation_intent("create_target_intent")
                parent = plugin.newDocument("Mnova Companion R1 disposable target")
                created_uuid = str(parent.uuid)
                created = snapshot()
                mark("target_created", snapshot=created)
                if not one_new_identity(before, created, created_uuid):
                    raise RuntimeError("Target creation changed existing inventory")
                if any(row_for(created, row["uuid"]) != row for row in before["documents"]):
                    raise RuntimeError("A pre-existing document state changed during creation")
                target_created = row_for(created, created_uuid)
                if (
                    type(target_created.get("page_count")) is not int
                    or target_created["page_count"] not in {0, 1}
                    or target_created.get("is_modified") is not False
                    or (
                        target_created["page_count"] == 0
                        and target_created.get("item_count", "missing") is not None
                    )
                    or (
                        target_created["page_count"] == 1
                        and (
                            type(target_created.get("item_count")) is not int
                            or target_created["item_count"] != 0
                        )
                    )
                ):
                    raise RuntimeError("Target creation did not observe a clean blank document")
                record["target_uuid"] = created_uuid
                record["target_creator_request"] = request["request_id"]
                write_json(MAILBOX / "ownership.json", record)
                if target_created["page_count"] == 0:
                    # The existing durable operation intent covers this second write.
                    mark("target_page_init_intent", target_uuid=created_uuid)
                    page = parent.newPage()
                    page = None  # Drop the child while its session parent remains live.
            elif operation == "close_target":
                target_uuid = record["target_uuid"]
                if target_uuid == sentinel_uuid:
                    raise RuntimeError("Target cannot be the protected sentinel")
                target_before = row_for(before, target_uuid)
                if (
                    target_before["is_modified"] is not False
                    or type(target_before.get("page_count")) is not int
                    or target_before["page_count"] != 1
                    or type(target_before.get("item_count")) is not int
                    or target_before["item_count"] != 0
                ):
                    raise RuntimeError("Only the owned clean blank target may be closed")
                if sentinel_before != record["sentinel_baseline"]:
                    raise RuntimeError("Sentinel changed before target close")
                require_target_creation(record)
                target = resolve(plugin, target_uuid)
                mutation_intent("close_target_intent", target_uuid=target_uuid)
                plugin.closeDocument(target)
                # No reads through target/child wrappers after close, no second cleanup.
                target = None
    after = snapshot()
    mark("after", snapshot=after, snapshot_sha256=digest(after))
    if operation == "create_target":
        if not one_new_identity(before, after, created_uuid):
            raise RuntimeError("Target initialization changed the expected inventory")
        target_after = row_for(after, created_uuid)
        if (
            type(target_after.get("page_count")) is not int
            or target_after["page_count"] != 1
            or type(target_after.get("item_count")) is not int
            or target_after["item_count"] != 0
            or target_after.get("is_modified") is not False
        ):
            raise RuntimeError("Target must be an observed clean blank single-page document")
    if operation == "dirty_action":
        sentinel_after = row_for(after, sentinel_uuid)
        if (
            sentinel_after["is_modified"] is not True
            or sentinel_after["page_count"] != sentinel_before["page_count"] + 1
            or sentinel_after["owned_content"] != sentinel_before["owned_content"]
        ):
            raise RuntimeError("The documented action did not prove a genuine dirty edit")
    if operation in {"create_sentinel", "create_target", "close_target"}:
        remaining = [
            row
            for row in before["documents"]
            if operation != "close_target" or row["uuid"] != target_uuid
        ]
        if any(row_for(after, row["uuid"]) != row for row in remaining):
            raise RuntimeError("A pre-existing document state changed")
    if operation == "close_target":
        if {r["uuid"] for r in after["documents"]} != {r["uuid"] for r in remaining}:
            raise RuntimeError("Close outcome unresolved; do not attempt another close")
        require_active(after, sentinel_uuid)
    return {
        "snapshot": after,
        "snapshot_sha256": digest(after),
        "acceptance": "pending_separate_read_only_invocation",
    }


def main() -> None:
    request = json.loads((MAILBOX / "request.json").read_text(encoding="utf-8"))
    validate_request(request)
    if request["operation"] != "inspect" and not MUTATIONS_ENABLED:
        raise RuntimeError(
            "Native lifecycle acceptance is incomplete; native mutations remain disabled"
        )
    if request["operation"] == "close_target" and not TARGET_CLOSE_ENABLED:
        raise RuntimeError("R1 target close failed; native close remains disabled")
    name = request["request_id"]
    started = MAILBOX / (name + ".started.json")
    final = MAILBOX / (name + ".receipt.json")
    if started.exists() or final.exists():
        return
    # Exclusive durable claim happens before native imports and every native call.
    with started.open("x", encoding="utf-8") as stream:
        json.dump({"request": request, "pid": os.getpid(), "started_unix": time.time()}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    receipt = {
        "schema_version": 1,
        "request": request,
        "state": "running",
        "stages": [],
        "embedded_python": platform.python_version(),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }

    def mark(stage: str, **details) -> None:
        receipt["stages"].append({"stage": stage, "time_unix": time.time(), **details})
        write_json(MAILBOX / (name + ".progress.json"), receipt)

    try:
        receipt["result"] = perform(request, mark)
        receipt["state"] = "completed"
    except Exception as exc:
        receipt.update(
            state="failed",
            error_type=type(exc).__name__,
            error=str(exc)[:2000],
            traceback=traceback.format_exc(limit=8),
        )
    finally:
        receipt["finished_unix"] = time.time()
        write_json(final, receipt)


if __name__ == "__main__":
    main()
