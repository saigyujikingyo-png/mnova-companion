# Assessment and next technical route

Status: **R0 PASSED BOUNDED; R1 FAILED; NATIVE WRITES DISABLED**.
Date: 2026-09-16. Shared baseline: Chembridge 2026-09-14.1.

The user approved development after the icon, installation and architecture
review. This phase repaired zero-page observation, established a visible owned
synthetic document with genuine dirty state, and ran one bounded target-close
experiment. That sequence removed the protected synthetic sentinel while leaving
the intended target present. Independent readback confirmed the failure. All
native writes stopped; the close route now has its own disabled gate.

## 1. Current assessment

| Area | Current result | Decision |
| --- | --- | --- |
| Icon and local host wiring | READY on this device | Icon, enabled personal plugin and non-editable runtime were verified independently of the checkout. Preserve the installed core. |
| Portable contracts/files/jobs | READY within tested scope | Six typed tools, durable jobs and staging/artifact checks remain useful infrastructure. Tests do not prove native workflows. |
| Native R0 prerequisites | PASSED BOUNDED | Main-window creation, unique ownership, synthetic attachment and a true dirty edit passed separate readback on the tested build. |
| Native lifetime R1 | FAILED | Clean target creation passed; close did not remove the target and the protected synthetic sentinel disappeared. Keep all native writes and the dedicated close path disabled. |
| Scientific workflow R2/R3 | BLOCKED | Native save/reopen, raw-data processing, integrals and exports are not accepted. |
| Cloud implementation checks | READY at recorded revisions | Reuse the existing environment. Record exact checkout results in [cloud evidence](CLOUD_SETUP.md); later code revisions need fresh checks. |
| Ordinary-user distribution | PARTIAL | Current-device installation works without a checkout, but its private venv uses the existing Python base. No general installer, update/removal or clean-device acceptance. |
| Hosts, models and delivery | UNVERIFIED beyond direct local protocol | No new host-model workflow, Terra max benchmark, remote adapter or received native artifact is accepted. |

The original cloud environment was restored through an existing signed-in
account without a duplicate or new credentials. Its actual setup tests and the
GitHub CI runs are separate from native Mnova acceptance.

## 2. Native evidence and unresolved cause

The [original cross-language experiment](NATIVE_API.md) failed with Windows
`c0000409` while a retained JS wrapper could outlive Python references. Stale
wrappers or destruction ownership remain hypotheses. The later [session
diagnosis](SESSION_DIAGNOSTIC_20260916.md) separately identified a null canvas
getter; a zero-page observation guard allowed session creation and readback.
Neither result establishes general safe lifetime semantics.

Assigning an existing session document to `Framework.activeDocument` returned as
a no-op. A distinct documented `action_File_New` main-window action then created
one visible document; ownership was claimed only after independent inventory.
A documented page action produced real `isModified=true`, with the owned
synthetic buffer unchanged. This is the bounded R0 pass.

In [R1](SESSION_LIFECYCLE_R1.md), the disposable target was independently verified
as clean, single-page and empty. The protected sentinel was genuinely dirty.
After the target-close sequence, the sentinel was absent and the target remained.
All three original document rows and the older synthetic buffer were preserved.
Only task-generated synthetic/blank documents were experiment inputs.

The failure interval includes target resolution and wrapper enumeration/release,
`closeDocument(target)`, clearing the target reference and fresh observation.
There was no intermediate state read to isolate those steps. Do not conclude
that the close API always closes the active document or that a vendor defect has
been proven. The postcondition detected the failed protection; it did not prevent
removal. No native retry or cleanup followed it.

The installed documentation declares `newDocument`, `documents` and
`closeDocument(aDoc)`, but does not settle Python wrapper return-value ownership,
window/session relationships, dirty-document prompt behavior or post-close
lifetime. [pybind11 ownership documentation](https://pybind11.readthedocs.io/en/stable/advanced/functions.html#return-value-policies)
explains why the binding's actual policy matters. A type name, `del` or
`gc.collect()` is insufficient evidence of a safe native destruction path.

## 3. Architecture and immediate containment

Retain the host-neutral Python core, six public tools, structured result schemas,
durable jobs, artifact hashes and thin host adapters. The native dispatcher stays
closed. The acceptance harness remains outside the installed wheel.

`MUTATIONS_ENABLED=False` disables shipped mutations. A second
`TARGET_CLOSE_ENABLED=False` gate rejects close at both acceptance entrypoints
before native imports or request claims, even if the first flag is privately
enabled. Tests using vendor doubles explicitly opt in both flags only to verify
historical guards, failure receipts and same/new-ID replay refusal. They cannot
accept the failed native route.

Keep failed intents, ownership records, snapshots and exact executed source.
The per-operation intent is flushed and fsynced; progress-stage JSON is atomically
replaced but is not separately fsynced. Do not describe every progress marker as
power-loss durable. No automatic cleanup is authorized by a failed postcondition.

## 4. Next technical gate

1. Establish documented session/window ownership and close semantics for the
   installed binding, with enough evidence to select an exact-target mechanism.
   Static source/documentation inspection comes before another native experiment.
2. Design an isolated diagnostic that can distinguish resolution, invocation,
   wrapper release and later observation. Retain process-instance fencing,
   exclusive intents, exact inventories and independent post-scope readback.
3. Consider an independently isolated Console executor only if its automation
   licence, invocation, process ownership, non-forwarding behavior, output and
   exit cleanup can be verified. The [Console product page](https://mestrelab.com/mnova-console)
   establishes availability, not those guarantees. A launcher PID alone is not
   isolation. Do not add Gears, a resident service or another model provider by
   default. No vendor support message has been sent; sending one needs explicit
   authorization.

Do not reactivate the failed close path, switch the active document and retry,
re-register an existing document or weaken the sentinel checks to obtain a pass.
No delivery estimate is credible until the native ownership contract is resolved.

## 5. Remaining acceptance order

| Stage | Required evidence |
| --- | --- |
| R1 replacement, currently blocked | Only the intended target disappears; protected dirty content and active selection survive; a later independent invocation succeeds without a crash, unexpected prompt handling or late destructor failure. |
| R2 save and fresh reopen | Nonempty native file with hash/size; reopened dimensions, nucleus, points, axes, data and annotations match; editability verified through an accepted lifecycle. |
| R3 one 1D vertical workflow | Authorized synthetic/public 1H fixture, explicit processing/reference/integrals, numerical tolerances, unchanged raw bytes, provenance and inspected native/PNG/PDF/table outputs. Record any automatic processing during import. |
| R4 connect accepted native work to jobs | Versioned typed operations, exact document/revision binding, one write per request, cooperative cancellation and reconciliation of unknown outcomes without replay. |
| R5 delivery and packaging | Host-received original bytes, openable native file, standalone runtime and clean-device install/update/remove preserving existing state and rollback. |
| R6 model and scoped release | Actual available Terra max then other advertised hosts/models; measured first-attempt success, corrections, calls, timing and available usage. Publish only passing routes. |

Do not broaden public operations, build hosted relays or claim scientific
capability while R1 remains failed. Cloud checks, installed-core protocol calls,
native execution, visual review, host attachments and release acceptance remain
separate evidence.
