# Mnova Companion lifecycle record

Record version: **1.0**. Observation date: **2026-09-19**.
Shared rule version: **2026-09-19.1**;
[runtime contract](../RUNTIME_LIFECYCLE.md): **1.0**.
Shared documents are pinned to published Chembridge commit
`922d95041b3b857f6ba11fbfb2817b18712ef605`; concurrent Hub drafts are not adopted.

Owner: one Astra Max Product owner, with Governance High review.
The verified handoff was accepted by governance on 2026-09-19; ownership is
**MIGRATED**. Private task identifiers and checkpoint locations remain outside
public source. Ownership transfer and rule adoption do not accept product
behavior or close [CB-2026-001](../governance/incidents/CB-2026-001.md).

## Source, package and evidence identity

Repository: [Mnova Companion](https://github.com/saigyujikingyo-png/mnova-companion).
Default and working branch: `codex/initial-preview`.
Current base commit: `7f09b68fb1f6e4f68528c0e827e2e12dbd5e61f0`, plus the
preserved, unpublished [P0 source increment](P0_EXECUTION.md).
Source version remains `0.1.0.dev1`; no release or package is produced by this
documentation change. The nine implementation hashes in the
[P0 receipt](../acceptance/p0_portable_20260916.json) still match.

The current-device installed package also reports `0.1.0.dev1`, but it is an
older implementation: its historical installation receipt binds
`e861d5297e8d9c1c17284998c25bb8ae363cacde`.
On 2026-09-19 its eight package source files still matched their RECORD
hashes/sizes; `execution.py` was absent. Plugin source/cache connection
configuration matched the retained installation identity.
Version text alone does not distinguish these two implementations.
[Installation evidence](INSTALLATION.md) remains separate from source checks.

The current readback covers Git identities, preserved source hashes, static
installed files and VM configuration. It does not include a fresh MCP invocation,
native call, VM start, installed upgrade or OS-event test. Historical portable,
CI, cloud, direct installed-protocol and native observations retain their
original dates and scopes.

## Components and owners

| Component / class | Current implementation | Startup and shutdown/crash owner | Scope and cardinality |
| --- | --- | --- | --- |
| Local MCP frontend / `on_demand_local_companion` | Implemented. `__main__.py` enters `server.main`; `server.py` constructs the service and runs stdio. Installed configuration selects isolated Python with `-I -m mnova_companion`. | Agent host launches its frontend; stdio/asyncio control transport lifetime. Project-specific drain, failed-initialization cleanup and in-flight EOF behavior remain unaccepted. | OS user, installed executable and selected runtime root. Multiple host frontends are allowed by the intended model; they do not establish multiple execution owners. |
| Portable job journal / supporting local component | P0 checkout implements typed fake attempts, receipts, leases and quarantine. It has no independent coordinator, queue worker, timeout monitor or automatic recovery loop. | Calling frontend invokes metadata operations. Store construction creates storage, not a worker. | Canonical resolved state root; OS-held metadata lock serializes transactions. One durable resource lease does not establish native process ownership. |
| Native adapter / `native_session_bound_bridge` | Developer-only harness; public native dispatch, global mutation and target-close gates remain disabled. | No accepted production launcher or cleanup owner. Native investigation is single-owner and serial within separately admitted scope. | Native session/document/attempt ownership must be proven independently. PID alone and a second launcher are insufficient. |
| Dedicated executor / planned `durable_job_service` | Not implemented or accepted. P0 admits only matching `portable_fake` profiles/handshakes. | No production supervisor exists to promise survival beyond frontend, host or OS exit. | Production session identity, authenticated IPC, process retirement and execution cardinality remain future gates. |
| Remote connector | No product tunnel, HTTP relay, remote binding or persistent connector is implemented. | No product remote supervisor/startup registration is provided. | Remote account/profile lifecycle is unimplemented; no single-profile daemon invariant is claimed from local stdio. |

Implementation references: [stdio](../src/mnova_companion/server.py),
[jobs](../src/mnova_companion/jobs.py),
[fake protocol](../src/mnova_companion/execution.py),
[staging/artifacts](../src/mnova_companion/artifact_store.py).
These links refer to the checkout. They do not describe the older installed
package as though it contained P0.

A narrow 2026-09-19 process sample found runtime-path Python frontends with the
agent host as parent. Task-to-process mapping and complete lifecycle ownership
were not established. The sample is not evidence of orphan leakage. No matching
product startup service/task was found in the bounded name/path scan.
No process was terminated, and no autostart requirement is inferred.

## Canonical state and authority

The frontend selects `MNOVA_COMPANION_HOME`, defaulting to the current user's
local application-data directory. The service separates state and artifacts;
input roots are owner-selected and default to an empty list. JobStore resolves
its state path. The artifact store rejects linked/reparse storage paths.
Cross-launcher canonical identity, Windows alias/case handling, frontend registry
and process start-identity fencing still need explicit lifecycle acceptance.

The OS-held metadata lock is distinct from durable `native.lock` and from
past-effect records. Metadata contention has a bounded retry; native execution
does not inherit that retry. P0 binds attempts to executor session, process
instance, fencing token, build, document and revision using fake identities.
Those comparisons are portable protocol evidence, not real native identity.

A dispatch consumes its attempt durably before allowing one fake effect. An
interruption after consumption never authorizes replay, including under a new
request key, session, process or restored environment. This is not a guarantee
of exactly-once execution. Unknown effects remain quarantined independently of
resource release. Fake reconciliation can establish a witnessed outcome while
the executor still requires witnessed retirement. Public reconcile is read-only
and accepts no client assertion of success.

Authority journals, consumed attempts, quarantine and sealed evidence must stay
outside VM snapshots and guest write access. Environment restore and reboot do
not clear these records. Local fsynced files and process-crash fixtures do not
establish universal power-loss durability. Cloud-synced/network state and
concurrent external edits are unsupported.

## Readiness, stop and recovery

The status tool reports installation metadata and explicitly unaccepted native
capabilities. Executable presence, tool discovery and a living frontend are
different observations from native readiness or licence entitlement.
No product health supervisor or bounded native readiness loop is implemented.

Tool calls run through `asyncio.to_thread`. Transport cancellation alone does
not establish that an already-running staging operation stopped.
EOF during work, failed initialization, abrupt exit, drain deadlines and staging
publication after connection loss require bounded portable fault tests before a
shutdown guarantee is made. Normal staging exceptions remove temporary pending
data; abrupt exit may leave it. A lost response followed by repeated open may
duplicate staging. No speculative pending-directory cleanup is authorized.

| Event | Implemented behavior / owner | Evidence or required gate |
| --- | --- | --- |
| Host connect/disconnect and EOF | Host starts stdio; SDK/asyncio manage transport. No native child is started by the frontend. | Historical direct installed protocol only. Current EOF/drain, failed-connect and in-flight staging behavior remain unverified. |
| Crash, retry and concurrent frontends | Metadata lock is OS-held; P0 keeps consumed attempts, unknown records and durable leases. No startup scan dispatches jobs or steals a lease by age/PID. | Historical portable P0 fixtures. Concurrent real-host frontends and failure cleanup need their own checks; preserve ambiguous owners. |
| Cancellation | Public observation/cancellation is metadata-based. P0 distinguishes unconsumed cancellation from requested cancellation after consumption. | No implied effect reversal, process kill, native close or safe-completion guarantee. Installed old behavior must be tested separately. |
| Boot, logon and reboot | No implemented product autostart service or automatic executor resumption. | Restart of the host/frontend does not authorize job replay. OS-event recovery and power-loss durability are unaccepted. |
| Network unavailable/restored | Current product is local stdio with local storage; no implemented remote reconnect loop. | Remote binding/retry behavior is unimplemented. Do not add a tunnel or promise service recovery from this record. |
| Sleep/resume, logoff and shutdown | No product-specific supervisor or accepted transition contract. | Preserve state and unknown effects; inspect/reconcile after interruption. No workstation transition was tested in this update. |
| Explicit stop or disabled startup | No product supervisor that should override an explicit stop; native sessions are not frontend-owned cleanup targets. | Host graceful-stop/abrupt-stop behavior remains unverified. Do not terminate unrelated sessions or host-owned frontends. |
| Upgrade, reinstall and rollback | Versioned runtime strategy is documented; P0 source has not upgraded the installed package. | Prove exact old/new runtime ownership and isolated state before migration; preserve configuration, unknown jobs and usable rollback. |
| Uninstall and retained data | Host plugin removal and separate private runtime/state cleanup have different scopes. | Removal/reinstall and retained-data policy need acceptance. No cleanup of user artifacts, native sessions or other plugins is implied. |

## Installation and state migration

[The installation guide](INSTALLATION.md) describes the private plugin
configuration and independently versioned runtime. The environment still
depends on an external Python base; it is not a self-contained fresh-device
package. This documentation adoption edits no installed launcher, host cache,
registration, runtime or state.

P0 writes version-2 records that the older strict installed reader cannot
consume. Existing historical records remain readable by the newer checkout,
but old active/unknown records do not gain invented fencing or completion
authority. Upgrade/rollback must keep older and P0 state isolated and prove
that old and new owners cannot operate incompatible records concurrently.
A runtime replacement alone is not state migration.

Before a later upgrade, record exact source/wheel/launcher identities, preserve
old runtime and state, reconcile proven owners, define compatibility and rollback,
and independently verify the installed protocol. Native, host, OS-event and
fresh-device acceptance remain separate. No silent P0 install is authorized.

## Native and I0 boundaries

The [R1 record](SESSION_LIFECYCLE_R1.md) remains FAILED. S/wrong-sentinel removal,
F/purecall-abort and A/zero-page getter failure remain separate incidents.
The unresolved R1 interval includes the pre-operation observer's sampling and
scope cleanup, target resolution, close, reference release and later observation.
A matching snapshot or a returned close call does not isolate the cause or prove
safe closure. Original receipts remain unchanged.

Both `MUTATIONS_ENABLED` and `TARGET_CLOSE_ENABLED` remain false.
Do not replay the failed sequence, change its ID to retry, force cleanup, or
claim isolation from a second launcher, `-w`, Python-only execution or a VM.

The 2026-09-19 [I0 readback](I0_ENVIRONMENT.md) is powered off with one NAT adapter
and only a fault snapshot. Manual recovery, guest installation/activation and
rollback results remain unknown. NAT is not accepted offline isolation.
I0 must establish the independent OS/environment boundary before a separately
admitted P1 bootstrap. Guest process identity, build/context and observer safety
belong to P1, not an invented native prerequisite for the earlier OS-only gate.

## Evidence ledger and next work

| Layer | Evidence as of 2026-09-19 | Still open |
| --- | --- | --- |
| Shared rules / ownership | Baseline adopted in source; verified Max takeover accepted by governance. | Runtime conformance and incident closure remain independent. |
| Portable P0 | Historical 2026-09-16: 341 tests and 42 subtests, two skips; nine implementation hashes still match. | New bounded lifecycle fault coverage on an exact candidate; no new test pass inferred from this doc edit. |
| CI / cloud | Historical exact-revision receipts at `7f09b68` / `77f6dac`; live GitHub state rechecked. | Dirty P0 is absent from those revisions; saved-cloud/model execution not rerun. |
| Installed package | Current static source/configuration integrity; old package lacks P0. | Fresh calls, lifecycle/upgrade/rollback and new-device acceptance. |
| Native / VM | Historical bounded R0; failed R1; current static I0 observation. | I0 acceptance, supported native lifecycle and scientific workflows. |
| Host / model / delivery | Historical direct installed MCP only; local artifact integrity is a separate layer. | Real host-model workflow, Terra max benchmark and received original files/attachments. |

The current increment is documentation-only: review the baseline adoption and
dated status correction while preserving the pre-existing dirty implementation
and its checkpoint. Missing manual VM results remain unknown and are not needed
to state that accurately.

Later portable lifecycle work needs its own bounded plan and checks for EOF,
failed initialization, in-flight cancellation, abrupt exit and ownership.
I0 needs the owner's outcome plus offline isolation, OS marker rollback,
external authority/quarantine canaries, sealed evidence export/readback and a
restored powered-off software baseline. P1, P2/R2, save/reopen, science and
delivery require their subsequent independent gates. This record enables none
of those operations.
