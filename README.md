# Mnova Companion

Independent open-source agent workflows for licensed MestReNova. This is a development checkpoint with native scientific writes disabled after a lifecycle acceptance failure. No stable or end-user release is available yet.

## Development state

See [status and acceptance](docs/STATUS.md). The first target is a protected native 1D NMR workflow on Windows, with explicit structured tool outputs and editable native artifacts. Native, portable, host and delivery checks are separate.

Read [shared development principles](DEVELOPMENT_PRINCIPLES.md) and [contributor instructions](AGENTS.md). Setup and executable checks will be listed here as they are implemented.

## Developer setup

Use Python 3.12 and uv, then run `uv sync --locked`. The matching cloud setup and maintenance entrypoint is `bash scripts/setup_codex_cloud.sh`. Dependencies are locked in `uv.lock`; the embedded Mnova interpreter remains separate. Ordinary-user packaging is not yet available.

Run the development MCP server with `uv run python -m mnova_companion`. It exposes status, help, authorised input staging, gated native requests, durable job observations and registered artifact access. Input staging does not open a native Mnova document. Select input roots through the owner-controlled `MNOVA_ALLOWED_INPUT_ROOTS` JSON-array environment setting; the default permits no input directories. `MNOVA_COMPANION_HOME` optionally selects the private local runtime directory.

## Verification

```text
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest -q
uv run python scripts/check_contracts.py
uv run python scripts/smoke_mcp.py
uv run python scripts/check_release.py
```

These checks exercise portable infrastructure and actual MCP stdio calls. They do not establish NMR processing, native save/reopen, an installed host/model workflow or received host attachments. See [contract coverage](docs/CONTRACT_COVERAGE.md) and [cloud setup](docs/CLOUD_SETUP.md).

Mnova Companion does not include MestReNova, vendor licences or university data. It is independent of Mestrelab and the University of Edinburgh.
