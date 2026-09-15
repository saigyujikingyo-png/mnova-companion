#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null 2>&1 || { echo 'Install uv in the development environment first.' >&2; exit 1; }
uv sync --locked --python 3.12
