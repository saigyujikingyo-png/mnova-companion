# Codex cloud development environment

Updated: 2026-09-15.

## Saved configuration

The environment **Chembridge / Mnova Companion** was created and saved through
the supported Codex Cloud environment interface. The saved detail and edit pages
were read back after creation.

| Setting | Saved value |
| --- | --- |
| Repository | `saigyujikingyo-png/mnova-companion` |
| Image | `universal` |
| Python version | `3.12` |
| Container cache | Enabled |
| Setup command | `bash scripts/setup_codex_cloud.sh` |
| Maintenance command | `bash scripts/setup_codex_cloud.sh` |
| Agent network preset | Common dependencies |
| Agent HTTP methods | `GET`, `HEAD`, `OPTIONS` |
| Extra domains | None required for the portable checks |
| Environment variables and secrets | None added |

The setup script installs the locked development dependencies with
`uv sync --locked --python 3.12`. Development source and dependencies remain in
the product's own cloud checkout; licensed MestReNova and private data are not
installed or copied into the container.

## Verification ledger

| Gate | State | Evidence |
| --- | --- | --- |
| Environment creation and saved setting readback | READY | Saved environment detail and edit pages show the matching repository and configuration. |
| Interactive container setup and maintenance | READY | On commit `e03deb0eabf45a4a9b057403d232037193848e93`, Python 3.12.13 created the virtual environment, setup installed 35 packages, maintenance audited the same 35 packages, and the UI reported `Test complete`. |
| Portable tests on the implementation commit | BLOCKED / NOT RUN IN CLOUD | Remote branch readback confirmed `e58824942c2fae86bd0f29b6fdb49f58f657e0dc`. The original browser session was no longer available when resuming; the remaining browser used a different signed-in account and could not load the saved environment. The initial setup pass is not a pass for this implementation revision. |
| Environment selector readback | READY | The Codex Cloud composer listed `Chembridge / Mnova Companion`; selecting it exposed `codex/initial-preview` as the selected branch. No task was submitted. |
| Actual model-based cloud task | UNVERIFIED | No task was created for this setup check. |
| Desktop dispatch to the environment | UNVERIFIED | Not exercised by environment creation. |
| Native MestReNova execution and editability | SEPARATE FAILED LIFECYCLE GATE | The native owner recorded a cross-engine document-destruction crash (`c0000409`). Native mutations remain disabled. Cloud setup does not resolve or supersede that failure; save/reopen/export remain unaccepted. |
| Agent host and end-user artifact delivery | UNVERIFIED | Require separate host and file-receipt checks. |

Configuration and portable cloud checks establish development readiness only.
They do not establish native software, scientific correctness, model, installer,
or host delivery acceptance. Other Chembridge environment results are not reused.

Account identifiers, environment identifiers and private UI/session records are
excluded from this public receipt.

## Implementation-revision checks still required

Restore access to the existing environment through its owning account. Do not
create a duplicate environment in another account merely to avoid the access
boundary. Inspect the cloud checkout for user changes before updating it; retain
any unrelated work and do not reset it. Then verify the actual checked-out commit
and run the following commands in that cloud checkout:

```bash
bash scripts/setup_codex_cloud.sh
.venv/bin/ruff check src tests scripts mnova_adapter
.venv/bin/ruff format --check src tests scripts mnova_adapter
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_contracts.py
.venv/bin/python scripts/smoke_mcp.py
.venv/bin/python scripts/check_release.py
```

These commands were not executed in the cloud for the implementation revision
at this checkpoint. Local or CI results, if separately recorded, must not be
described as results from this interactive Codex cloud container.
