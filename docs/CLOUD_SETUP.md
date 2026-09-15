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
| Portable tests on a recorded commit | PENDING | Awaiting the implementation commit and test run. |
| Environment selector readback | READY | The Codex Cloud composer listed `Chembridge / Mnova Companion`; selecting it exposed `codex/initial-preview` as the selected branch. No task was submitted. |
| Actual model-based cloud task | UNVERIFIED | No task was created for this setup check. |
| Desktop dispatch to the environment | UNVERIFIED | Not exercised by environment creation. |
| Native MestReNova execution and editability | UNVERIFIED | Require a licensed native execution device and separate evidence. |
| Agent host and end-user artifact delivery | UNVERIFIED | Require separate host and file-receipt checks. |

Configuration and portable cloud checks establish development readiness only.
They do not establish native software, scientific correctness, model, installer,
or host delivery acceptance. Other Chembridge environment results are not reused.

Account identifiers, environment identifiers and private UI/session records are
excluded from this public receipt.
