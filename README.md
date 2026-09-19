# Mnova Companion

Independent open-source agent workflows for licensed MestReNova. This is a development checkpoint with native scientific writes disabled while lifecycle acceptance remains incomplete. No stable or end-user release is available yet.

## Development state

See [status and acceptance](docs/STATUS.md). The first target is a protected native 1D NMR workflow on Windows, with explicit structured tool outputs and editable native artifacts. Native, portable, host and delivery checks are separate.

The approved [C3/P0 increment](docs/P0_EXECUTION.md) hardens portable dispatch,
receipts and recovery using fake execution. Native calls remain disabled and
source changes do not automatically upgrade the installed runtime.

The [product lifecycle record](docs/LIFECYCLE.md) adopts shared baseline
2026-09-19.1 and separates current stdio behavior, unpublished portable P0,
the older installed package and remaining lifecycle gates. The dated
[I0 environment record](docs/I0_ENVIRONMENT.md) reports a powered-off guest
with a NAT setup exception and unknown manual completion; I0 is not accepted.

The [current-device Codex installation](docs/INSTALLATION.md) includes the [icon](assets/DESIGN.md) and an independently installed runtime. After the original [R0 failure](docs/SESSION_LIFECYCLE_R0.md), the [zero-page diagnostic](docs/SESSION_DIAGNOSTIC_20260916.md) established guarded creation and synthetic readback. The subsequent [main-window R0 route](docs/SESSION_LIFECYCLE_R1.md) established a visible owned document and genuine dirty state. R1 failed: the target-close sequence removed the protected synthetic sentinel while leaving its intended target present. The close path is independently disabled; later scientific features remain blocked. See the [technical route](docs/NEXT_TECHNICAL_ROUTE.md).

Read [shared development principles](DEVELOPMENT_PRINCIPLES.md) and [contributor instructions](AGENTS.md). The [native investigation](docs/NATIVE_API.md) records the supported metadata route and failed lifecycle gate.

## Developer setup

Use Python 3.12 and uv, then run `uv sync --locked`. The matching cloud setup and maintenance entrypoint is `bash scripts/setup_codex_cloud.sh`. Dependencies are locked in `uv.lock`; the embedded Mnova interpreter remains separate. Ordinary-user packaging is not yet available.

Run the development MCP server with `uv run python -m mnova_companion`. It exposes status, help, authorised input staging, gated native requests, durable job observations and registered artifact access. Input staging does not open a native Mnova document. Select input roots through the owner-controlled `MNOVA_ALLOWED_INPUT_ROOTS` JSON-array environment setting; the default permits no input directories. `MNOVA_COMPANION_HOME` optionally selects the private local runtime directory.

## Verification

```text
uv run ruff check src tests scripts mnova_adapter
uv run ruff format --check src tests scripts mnova_adapter
uv run pytest -q
uv run python scripts/check_contracts.py
uv run python scripts/smoke_mcp.py
uv run python scripts/check_release.py
```

These checks exercise portable infrastructure and actual MCP stdio calls. They do not establish NMR processing, native save/reopen, an installed host/model workflow or received host attachments. See [contract coverage](docs/CONTRACT_COVERAGE.md) and [cloud setup](docs/CLOUD_SETUP.md).

Mnova Companion does not include MestReNova, vendor licences or university data. It is independent of Mestrelab and the University of Edinburgh.
