"""Read-only, packaged Mnova feasibility probe; run inside Mnova only.

The ignored repository mailbox is an acceptance harness, not production IPC.
Native mutations remain disabled after the lifecycle gate failed.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import time
import traceback
from pathlib import Path

MAILBOX = Path(__file__).resolve().parents[1] / ".local" / "native"


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    os.replace(temporary, path)


def document_inventory(plugin) -> list[dict]:
    """Read identity/counts only; never read unrelated scientific content."""
    inventory = []
    for doc in plugin.documents():
        page_count = int(doc.pageCount)
        entry = {
            "identity_hash": hashlib.sha256(str(doc.uuid).encode("utf-8")).hexdigest(),
            "page_count": page_count,
            "page_item_count": None,
        }
        if page_count == 0:
            # Avoid pageItems access when the document has no page.
            entry["page_observation"] = "not_run_no_pages"
        else:
            entry["page_item_count"] = len(doc.pageItems())
        inventory.append(entry)
    return inventory


def probe() -> dict:
    from MnovaDocument import Document, DocumentPlugin
    from MnovaFramework import Framework, Serialization
    from MnovaNMR import NMRItem, NMRPlugin, NMRSpectrum

    framework = Framework.instance
    plugin = DocumentPlugin.instance
    before = document_inventory(plugin)
    capability_objects = {
        "Document": Document,
        "DocumentPlugin": DocumentPlugin,
        "Framework": Framework,
        "Serialization": Serialization,
        "NMRItem": NMRItem,
        "NMRSpectrum": NMRSpectrum,
        "NMRPlugin": NMRPlugin,
    }
    after = document_inventory(plugin)
    return {
        "software_version": list(framework.version),
        "embedded_python": platform.python_version(),
        "documents_before": before,
        "documents_after": after,
        "unrelated_document_inventory_preserved": before == after,
        "capabilities": {
            name: sorted(attr for attr in dir(obj) if not attr.startswith("_"))
            for name, obj in capability_objects.items()
        },
        "licence_state": "unknown_not_probed",
        "native_scientific_execution": "not_run",
    }


def main() -> None:
    request_path = MAILBOX / "request.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if set(request) != {"schema_version", "request_id", "operation"}:
        raise ValueError("Unexpected acceptance request fields")
    request_id = request["request_id"]
    if request["schema_version"] != 1 or not isinstance(request_id, str):
        raise ValueError("Invalid acceptance request")
    if (
        not request_id.isascii()
        or not request_id.replace("-", "").isalnum()
        or len(request_id) > 80
    ):
        raise ValueError("Invalid acceptance request identity")
    if request["operation"] != "probe":
        raise ValueError("Native mutation disabled: owned-document lifecycle gate failed")
    result_path = MAILBOX / (request_id + ".receipt.json")
    started_path = MAILBOX / (request_id + ".started.json")
    if started_path.exists() or result_path.exists():
        return
    receipt = {
        "schema_version": 1,
        "request_id": request_id,
        "operation": request["operation"],
        "started_unix": time.time(),
        "state": "running",
        "scope": "native_feasibility_only",
    }
    write_json(started_path, receipt)
    try:
        receipt["result"] = probe()
        receipt["state"] = "completed"
    except Exception as exc:
        receipt["state"] = "failed"
        receipt["error_type"] = type(exc).__name__
        receipt["error"] = str(exc)[:2000]
        receipt["traceback"] = traceback.format_exc(limit=8)
    finally:
        receipt["finished_unix"] = time.time()
        write_json(result_path, receipt)


if __name__ == "__main__":
    main()
