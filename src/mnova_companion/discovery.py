"""Read installation metadata without starting Mnova or reading licence files."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path


def _file_version(path: Path) -> str | None:
    """Read the file version string without executing the binary."""
    try:
        version = ctypes.windll.version
        length = version.GetFileVersionInfoSizeW(str(path), None)
        if not length:
            return None
        buffer = ctypes.create_string_buffer(length)
        if not version.GetFileVersionInfoW(str(path), 0, length, buffer):
            return None
        pointer, size = ctypes.c_void_p(), ctypes.c_uint()
        if not version.VerQueryValueW(
            buffer, "\\VarFileInfo\\Translation", ctypes.byref(pointer), ctypes.byref(size)
        ):
            return None
        translation = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ushort))
        key = f"\\StringFileInfo\\{translation[0]:04x}{translation[1]:04x}\\FileVersion"
        if version.VerQueryValueW(buffer, key, ctypes.byref(pointer), ctypes.byref(size)):
            return ctypes.wstring_at(pointer, size.value).rstrip("\0")[:240]
    except (OSError, ValueError, AttributeError):
        pass
    return None


def discover_installation() -> dict:
    if sys.platform != "win32":
        return {
            "installation_present": False,
            "executable_present": False,
            "registered_version": None,
            "executable_version": None,
            "version_source": "unavailable",
        }
    import winreg

    candidates = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for suffix in (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ):
            try:
                with winreg.OpenKey(hive, suffix) as root:
                    for index in range(winreg.QueryInfoKey(root)[0]):
                        with winreg.OpenKey(root, winreg.EnumKey(root, index)) as key:
                            try:
                                name = winreg.QueryValueEx(key, "DisplayName")[0]
                            except OSError:
                                continue
                            if "mestrenova" not in name.lower() and "mnova" not in name.lower():
                                continue
                            try:
                                version = str(winreg.QueryValueEx(key, "DisplayVersion")[0])[:240]
                            except OSError:
                                version = None
                            candidates.append(version)
            except OSError:
                continue
    # This return contains registration observations, never entitlement claims.
    executable = Path(os.environ.get("LOCALAPPDATA", "")) / (
        "Programs/Mestrelab Research/Mnova/MestReNova.exe"
    )
    file_version = _file_version(executable) if executable.is_file() else None
    registered = candidates[0] if candidates else None
    return {
        "installation_present": bool(candidates) or executable.is_file(),
        "executable_present": executable.is_file(),
        "registered_version": registered,
        "executable_version": file_version,
        "version_source": (
            "registry_and_file"
            if registered and file_version
            else "file_metadata"
            if file_version
            else "registry"
            if registered
            else "unavailable"
        ),
    }
