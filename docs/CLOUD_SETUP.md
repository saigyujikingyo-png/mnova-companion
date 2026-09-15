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
| Interactive container setup and maintenance | READY | Latest checked code revision `9effac312d355bb569a3352676c7761bdfb3b6d1`: Python 3.12.13 installed 35 locked packages; maintenance audited the same 35. UI reported `Test complete`; original saved commands were restored and read back. |
| Portable tests on the implementation commit | READY | Exact `9effac312d355bb569a3352676c7761bdfb3b6d1`, clean before/after: Ruff, formatting, 171 tests plus 42 subtests, contracts, actual MCP stdio and source preflight passed; four Windows-only tests skipped. |
| Environment selector readback | READY | The Codex Cloud composer listed `Chembridge / Mnova Companion`; selecting it exposed `codex/initial-preview` as the selected branch. No task was submitted. |
| Actual model-based cloud task | UNVERIFIED | No task was created for this setup check. |
| Desktop dispatch to the environment | UNVERIFIED | Not exercised by environment creation. |
| Native MestReNova execution and editability | SEPARATE FAILED LIFECYCLE GATE | Both the earlier standalone cleanup and the later session R0 creation stage failed. Native mutations remain disabled. Cloud checks do not resolve either failure; see [R0 result](SESSION_LIFECYCLE_R0.md). |
| Agent host and end-user artifact delivery | UNVERIFIED | Require separate host and file-receipt checks. |

Configuration and portable cloud checks establish development readiness only.
They do not establish native software, scientific correctness, model, installer,
or host delivery acceptance. Other Chembridge environment results are not reused.

Account identifiers, environment identifiers and private UI/session records are
excluded from this public receipt.

## Access recovery and implementation-revision checks

### Resolved browser access issue

At 18:56 UTC the available Edge session returned no matching Mnova environment
and the saved URL reported an error loading the environment. That observation
did not establish a service failure or require creating another environment.

Following renewed user authorization, the browser inventory was rediscovered.
A connected Chrome session was now available. The account submenu in the
ChatGPT home page exposed two existing signed-in accounts. Selecting the account
corresponding to the original environment creator restored access to the same
saved **Chembridge / Mnova Companion** environment at 19:07 UTC. The repository,
setup and maintenance scripts, cache and network settings were read back on its
edit page, and its interactive terminal was started.

No password, MFA code, cookie or token was read or entered. No account security
settings were changed and no duplicate environment was created. If this happens
again, check the existing account submenu before concluding that the original
environment needs to be recreated.

### Earlier core verification

The newly provisioned cloud checkout already contained the requested commit, so
no reset, checkout overwrite or pull was needed. A bounded script first printed
and asserted its exact SHA and clean status, then executed the following existing
checks with shell `time` measurements and failure-on-error enabled:

```bash
bash scripts/setup_codex_cloud.sh
.venv/bin/ruff check src tests scripts mnova_adapter
.venv/bin/ruff format --check src tests scripts mnova_adapter
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_contracts.py
.venv/bin/python scripts/smoke_mcp.py
.venv/bin/python scripts/check_release.py
```

| Check | Observed result | Shell real time |
| --- | --- | --- |
| Locked setup | 38 packages resolved; 35 packages installed | 3.524 s |
| Ruff lint | All checks passed | 0.044 s |
| Ruff formatting | 17 files already formatted | 0.045 s |
| Pytest | 52 passed, 4 skipped, 42 subtests passed; pytest reported 1.99 s | 3.537 s |
| Contract catalog | 6 tool contracts; 19,898 UTF-8 schema bytes | 0.626 s |
| MCP smoke | Actual stdio subprocess; 6 tools, structured/text parity and error branches passed | 4.488 s |
| Release source preflight | Tracked development manifest/privacy checks passed | 0.116 s |

The four skipped tests cover one Windows junction case and three Windows
short-path alias cases. They were not executed or accepted on this Linux cloud
container. Schema bytes are not billing tokens; the MCP smoke check is protocol
evidence, not a host-model or native acceptance test.

The script's observed UTC timestamps were **2026-09-15 19:12:05** and
**19:12:18**, an approximately 13-second interval with one-second timestamp
precision. This interval covers the commands and their setup, not browser access
recovery or cloud-container provisioning. After the checks, `git status --short`
remained empty. The environment then ran its normal maintenance command,
resolving 38 packages in 8 ms and auditing 35 packages in 0.78 ms, followed by
`Test complete`.

The interactive input box initially counted read-only commands without reliably
displaying their execution output. Therefore, the complete check script was run
through the environment's supported **rerun setup script** control. UI command
counts are not used as pass evidence. The temporary setup text was restored to
`bash scripts/setup_codex_cloud.sh` after the run. Returning to the saved detail
page confirmed that both persisted setup and maintenance commands still had
that original value, with the matching repository and zero model tasks. The
temporary check harness was not saved as environment configuration.

### Earlier setup evidence

The initial environment creation separately passed setup and maintenance on
`e03deb0eabf45a4a9b057403d232037193848e93`. That earlier result is retained as
historical setup evidence; the implementation-revision results above come from
the actual later cloud run and do not reuse local or CI results.

For future checks, inspect the cloud checkout for user changes before updating
it, preserve unrelated work, and record the actual checked-out commit. Cloud
verification of later revisions requires a corresponding run; this receipt
does not automatically cover commits made after the recorded SHA.

## R0 implementation checkpoint: latest cloud verification

The existing recovered browser session accessed the same environment directly.
No account exploration, new environment or model task was needed. Its official
setup-test route provisioned a fresh clone and asserted the exact commit
**`9effac312d355bb569a3352676c7761bdfb3b6d1`** and clean working tree before any
check. This revision includes the disabled R0/R1 harness and current-process
content-read protection; the installed runtime core is unchanged.

| Check | Observed result | Shell real time |
| --- | --- | --- |
| Locked setup | 38 resolved, 35 installed; Python 3.12.13 | 4.728 s |
| Ruff lint | Passed | 0.125 s |
| Ruff formatting | 19 files already formatted | 0.065 s |
| Pytest | 171 passed, 4 Windows-only skips, 42 subtests; pytest 4.25 s | 6.253 s |
| Contracts | 6 tools; 19,898 UTF-8 schema bytes | 1.036 s |
| Actual MCP stdio | Structured/text parity and error branches passed | 6.976 s |
| Source preflight | Tracked manifest/privacy checks passed | 0.234 s |

The script ran from **2026-09-15 19:46:19 UTC to 19:46:39 UTC**, approximately
20 seconds at the recorded timestamp precision. Container preparation and the
following maintenance are outside that interval. Git status remained clean.
Maintenance resolved 38 packages in 21 ms and audited 35 in 2 ms; the UI displayed
`Test complete`.

Afterward, the temporary setup text was restored. The edit fields and persisted
detail page showed both setup and maintenance as `bash scripts/setup_codex_cloud.sh`,
the original repository/image/cache and zero tasks. No temporary harness was
saved as configuration. Private UI evidence remains outside public source.

For the same `9effac3` revision, independent [GitHub CI](https://github.com/saigyujikingyo-png/mnova-companion/actions/runs/35015234860)
passed on Windows (175 tests, 44 subtests) and Ubuntu (171 tests, four skips,
42 subtests). These are separate CI and cloud-container observations. Neither
executed licensed Mnova, accepted the native crash, invoked a host model or
verified native artifact delivery. Later documentation-only receipt commits do
not change the code covered by this recorded run.
