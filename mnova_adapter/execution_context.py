"""Read-only Windows execution-context probe, run by Mnova's Python entrypoint.

No document wrappers, JavaScript, GUI input, memory reads or native writes.
The private request binds a known process instance and its observed main window.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import time
from pathlib import Path

MAILBOX = Path(__file__).resolve().parents[1] / ".local" / "native" / "execution-context"


def validate_request(request: dict) -> None:
    fields = {"schema_version", "request_id", "pid", "process_created_filetime", "window_handle"}
    if not isinstance(request, dict) or set(request) != fields:
        raise ValueError("Unexpected context request fields")
    name = request["request_id"]
    if (
        type(request["schema_version"]) is not int
        or request["schema_version"] != 1
        or not isinstance(name, str)
        or not name
        or len(name) > 80
        or not name.isascii()
        or not name.replace("-", "").isalnum()
    ):
        raise ValueError("Invalid context request identity")
    for field in ("pid", "process_created_filetime", "window_handle"):
        if type(request[field]) is not int or not 0 < request[field] < 2**64:
            raise ValueError("Invalid process/window binding")


def read_context(window_handle: int) -> dict:
    """Read only documented OS metadata; never dereference a vendor wrapper."""
    if os.name != "nt":
        raise OSError("Windows-only native diagnostic")
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetCurrentThreadId.argtypes = []
    kernel.GetCurrentThreadId.restype = wintypes.DWORD
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    kernel.GetModuleFileNameW.restype = wintypes.DWORD
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    times = [wintypes.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(kernel.GetCurrentProcess(), *(ctypes.byref(t) for t in times)):
        raise ctypes.WinError(ctypes.get_last_error())
    image = ctypes.create_unicode_buffer(32768)
    size = kernel.GetModuleFileNameW(None, image, len(image))
    if not 0 < size < len(image):
        raise RuntimeError("Could not resolve current executable")
    owner_pid = wintypes.DWORD()
    window_thread = int(user.GetWindowThreadProcessId(window_handle, ctypes.byref(owner_pid)))
    if not window_thread:
        raise ctypes.WinError(ctypes.get_last_error())
    return {
        "pid": os.getpid(),
        "process_created_filetime": times[0].dwLowDateTime | (times[0].dwHighDateTime << 32),
        "image_name": Path(image.value).name,
        "script_thread_id": int(kernel.GetCurrentThreadId()),
        "window_thread_id": window_thread,
        "window_pid": int(owner_pid.value),
    }


def verify_context(request: dict, observed: dict) -> dict:
    if (
        observed["pid"] != request["pid"]
        or observed["process_created_filetime"] != request["process_created_filetime"]
        or observed["window_pid"] != request["pid"]
        or observed["image_name"].casefold() != "mestrenova.exe"
    ):
        raise RuntimeError("Observed executable/process/window does not match the request")
    return observed | {
        "same_thread": observed["script_thread_id"] == observed["window_thread_id"],
        "scope": "os_execution_context_only",
        "document_access": "not_run",
        "native_writes": "not_run",
    }


def main() -> None:
    request = json.loads((MAILBOX / "request.json").read_text(encoding="utf-8"))
    validate_request(request)
    name = request["request_id"]
    started, final = [MAILBOX / (name + suffix) for suffix in (".started.json", ".receipt.json")]
    if started.exists() or final.exists():
        return
    with started.open("x", encoding="utf-8") as stream:
        json.dump({"request": request, "started_unix": time.time()}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    receipt = {
        "schema_version": 1,
        "request_id": name,
        "embedded_python": platform.python_version(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    try:
        receipt["result"] = verify_context(request, read_context(request["window_handle"]))
        receipt["state"] = "completed"
    except Exception as exc:
        receipt.update(state="failed", error_type=type(exc).__name__, error=str(exc)[:1000])
    receipt["finished_unix"] = time.time()
    temporary = final.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, final)


if __name__ == "__main__":
    main()
