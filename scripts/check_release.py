"""Check the development package for accidental private/runtime material."""

import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
assert manifest["name"] == "mnova-companion"
assert manifest["license"] == "MIT"
assert (root / "LICENSE").is_file()
files = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
for name in filter(None, files):
    path = Path(name)
    assert not any(part in {".local", ".venv", "node_modules"} for part in path.parts), name
    assert path.suffix.lower() not in {".lic", ".exe", ".dll", ".mnova"}, name
    if path.suffix.lower() in {".md", ".py", ".json", ".toml", ".yml"}:
        text = (root / path).read_text(encoding="utf-8")
        assert ("[" + "TODO:") not in text, name
        assert "C:\\Users\\adobook" not in text, name
print("PASS: tracked development source manifest/privacy checks.")
print("Scope: source preflight only; no native, installed-host or stable-release claim.")
