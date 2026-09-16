# Main-window R0 and bounded R1 lifecycle acceptance

Date: 2026-09-16. Native build **17.0.1-41952**, embedded Python **3.11.15**.
The public native dispatcher and shipped acceptance mutation flag remain disabled.

## Accepted R0 prerequisite

The [zero-page diagnosis](SESSION_DIAGNOSTIC_20260916.md) fixed snapshot access but
did not make the session-only document visible. Assigning that existing document
to `Framework.activeDocument` returned without changing the active document.
That completed no-op was not replayed, and `addDocument` was not called on it.

A distinct, documented main-window route was then tested once:
`Framework.getAction("action_File_New").trigger()`. The entire action scope
returned before a separate native inspection. That inspection proved exactly one
new UUID, one clean blank page, agreement between both active-document observers,
and unchanged rows for all three prior documents. The native interface displayed
the new document tab. Ownership was claimed only after that independent result.

The new owned document received the same original two-singlet fixture through
Python, with the parent retained while the child was attached. A separate read
confirmed 16,384 points, 1H at 400 MHz and the expected real-buffer hash. Direct
attachment still left `isModified=false`, so nonempty content was not counted as
an unsaved edit.

The documented `action_Edit_CreateNewPage` action then added a second page to the
active owned document. Mnova reported **`isModified=true`**, and the Undo control
became enabled. A separate post-scope invocation returned the identical complete
snapshot, including the unchanged spectrum buffer. Another read using the older
ownership scope verified all three prior document rows and the earlier synthetic
buffer remained unchanged. See the [bounded R0 receipt](../acceptance/session_gui_r0_20260916.json).

These observations accept this R0 prerequisite on the tested build only. The
spectrum's displayed layout, licence entitlement and scientific processing were
not accepted from document-window presence or in-memory buffers.

## R1 target contract

The disposable target must have exactly one observed clean page and zero items.
Creation must preserve all prior rows, including the genuinely dirty sentinel.
If the new session document starts with zero pages, page creation is a distinct
recorded step on the proven owned parent, followed by a fresh exact inventory and
state check. An unknown count is never converted into zero.

Close requires a completed matching target-creation receipt, current exact
snapshot, the unchanged dirty sentinel, matching active-document observations and
the observed clean one-page target. It is called once; old target/child wrappers
are not read after close. A later independent native invocation is required for
acceptance. Failed or incomplete creation never authorizes automatic cleanup.

## R1 result: FAILED

Target creation and a separate invocation both observed exactly one new clean
single-page document with zero items. Every prior row, including the dirty
synthetic sentinel, remained unchanged. The target's page initialization and
completed creator receipt therefore passed their bounded prerequisite checks.

One `close_target` sequence then ran against that recorded target. Its final
snapshot contained four documents instead of five: **the protected dirty
synthetic sentinel was absent, while the intended target remained present**.
The active document returned to the startup blank. The harness reported
`Owned document missing or ambiguous` and retained its failed receipt and final
snapshot. The after-state guard detected the loss; it did not prevent it.

A later independent invocation reproduced the same after-state snapshot.
Another inspection in the original ownership scope verified that all three
original document rows and the earlier synthetic spectrum buffer were unchanged.
Mnova remained responsive; no crash was observed. The removed document was
created by this task from synthetic data. No user scientific file was an input
to the experiment.

The exact executed lifecycle source had SHA-256
`9f6a1c89073507b2ca5cf999baab5488edcc82da14bd543f524091ea3d4ed34d`.
Its immutable private copy, claims, ownership records and raw receipts are
retained outside public source. See the [sanitized R1 receipt](../acceptance/session_lifecycle_r1_20260916.json).

### Attribution boundary

The last known-good snapshot preceded target resolution. No independent snapshot
separated `resolve(plugin, target_uuid)`, `closeDocument(target)`, clearing the
target wrapper and the first fresh observation. That entire sequence is the
unresolved failure interval, including wrapper enumeration and release during
resolution. The call and subsequent observation returned, but this does not prove
that the close API alone ignored its argument, nor establish a general vendor
defect. No alternate native close or activation sequence was attempted afterward.

### Containment and next gate

All native writes stopped after this failure. Both acceptance entrypoints now
check a separate `TARGET_CLOSE_ENABLED=False` gate before native imports or a
request claim, even if a private runner enables the global mutation flag.
`MUTATIONS_ENABLED=False` and the public native dispatcher remain disabled.
Portable doubles verify rejection and preservation of a wrong-removal failure
receipt, including refusal to replay with the same or a new request identifier.
Those tests do not establish safe native close semantics.

R1 is **FAILED**. R2 save/reopen, scientific processing, exports and end-user
release remain blocked. No automatic target cleanup was attempted. The next
technical gate is a documented and independently testable relationship between
session documents, document windows, wrapper ownership and exact-target closure.
Changing the active document and retrying would not resolve that contract. Any
replacement experiment needs isolated failure intervals and its own acceptance;
the failed sequence must not be replayed. No vendor support message was sent.
