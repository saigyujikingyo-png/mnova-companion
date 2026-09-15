# Mnova Companion

Independent open-source agent workflows for licensed MestReNova. Implementation is in progress; no stable or end-user release is available yet.

## Development state

See [status and acceptance](docs/STATUS.md). The first target is a protected native 1D NMR workflow on Windows, with explicit structured tool outputs and editable native artifacts. Native, portable, host and delivery checks are separate.

Read [shared development principles](DEVELOPMENT_PRINCIPLES.md) and [contributor instructions](AGENTS.md). Setup and executable checks will be listed here as they are implemented.

## Developer setup

Use Python 3.12 and uv, then run `uv sync --locked`. The matching cloud setup and maintenance entrypoint is `bash scripts/setup_codex_cloud.sh`. Dependencies are locked in `uv.lock`; the embedded Mnova interpreter remains separate. Ordinary-user packaging is not yet available.

Mnova Companion does not include MestReNova, vendor licences or university data. It is independent of Mestrelab and the University of Edinburgh.
