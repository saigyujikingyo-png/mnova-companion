# Native API evidence and boundaries

Evidence date: 2026-09-15. Observed Mnova build: **17.0.1-41952** on Windows.
Observed embedded Python: **3.11.15**. The external core uses a separate Python
environment. No packages were installed into the embedded interpreter.

## Result

**P0 native lifecycle: FAILED. Native mutations are disabled.** Read-only Python
bootstrap succeeded. A bounded synthetic experiment confirmed creation and
readback of native spectral data. It did not establish a safe production workflow.
The cross-language lifecycle experiment terminated the native process with Windows
exception `c0000409`. Native processing, save/reopen and exports are **NOT_RUN**.

The public record is `acceptance/native_20260915.json`. Private raw receipts,
progress, synthetic fixtures, event metadata and the exact experimental source
remain in ignored `.local/native/`. No private identifiers are in the public record.

## Documented interfaces versus actual observations

Installed vendor documentation was read in place. Paths below are relative to the
Mnova installation; the files are not redistributed.

| Interface | Installed documentation | Actual observation |
| --- | --- | --- |
| Python script execution | `examples/scripts/py/applicationInfo.py` and Python API documentation | Passing the packaged `.py` path to `MestReNova.exe` ran `main()` under the embedded interpreter. Repeated invocation executed in the existing process. |
| Version and document inventory | `documents/python/MnovaFramework.html`, `MnovaDocument.html` | Version, document UUID hashes and page/item counts read successfully. The initial metadata-only probe preserved inventory. |
| Standalone `Document()` and explicit lock/unlock | `documents/python/MnovaDocument.html`, `MnovaFramework.html` | A standalone document remained outside the session list. An owned nonempty sentinel stayed unchanged through creation, locking, attachment, unlocking and Python reference release. |
| Synthetic `NMRItem` XML constructor | `documents/python/MnovaNMR.html` | Original two-singlet synthetic XML created a 1D native spectrum with 16,384 points, 400 MHz, 1H, and peaks at 2 and 5 ppm. The real buffer and peak attributes were read back. |
| Spectrum title | `documents/python/MnovaNMR.html` | `NMRSpectrum.title` is read-only; assigning to it raised `AttributeError`. |
| Processing and explicit integrals | `documents/python/MnovaNMR.html` | API names were inspected. Execution was not reached. |
| Native `Document.save(path)` and `Document(path)` | `documents/python/MnovaDocument.html` | Documented only. Neither native save nor fresh disk readback was reached. |
| PDF/PNG serialization | `documents/python/MnovaFramework.html`; installed script examples | Documented candidate only. No export attempt was reached. |
| JS `Document.destroy()` | `documents/scripts/mnova-scripting.html#Document.destroy` | A guarded cross-language release attempt ended in native process failure; this route is rejected. |
| JS `Document.isModified` and `Text.plainText` | `documents/scripts/mnova-scripting.html` | Both read/modified only the owned sentinel. `isModified` stayed false after native Python content attachment and after JS marker-text modification. A genuinely dirty-document protection gate is still unverified. |

These observations apply to this build and this bounded experiment. They do not
prove module entitlement, correctness on experimental data, FID processing,
multiplet analysis, assignment, unattended use, other builds, or host delivery.
Licence contents and licence secrets were not inspected. No Gears or Console
capability is assumed.

## Lifecycle failure, scope and attribution

1. An early synthetic experiment failed on the read-only title setter. After its
   entire cleanup block the original empty default document was absent. There was
   no intermediate inventory sufficient to attribute that result to a specific
   call. `closeDocument(standalone)` was removed from subsequent experiments.
2. A separate, clearly marked, nonempty synthetic session sentinel was created.
   It remained unchanged throughout a standalone Python reference-release probe.
   Dropping Python references was not treated as proof of native destruction.
3. The next experiment retained the exact locked standalone document in fixed JS.
   It verified the UUID and absence from the session list, unlocked in Python,
   and dropped Python wrappers. Before every step the sentinel still matched.
4. The release helper was then entered. It was designed to recheck the retained
   UUID, reject session/active documents, call `destroy()` on that handle and clear
   it. No completion receipt returned. The last persisted stage was
   `python_wrappers_released`.
5. Windows Application Error recorded `MestReNova.exe` version `17.0.1.41952`,
   fault module `ucrtbase.dll`, exception `c0000409` at
   **2026-09-15T16:48:29.7979809Z**. The native process was absent afterward.

The evidence does not distinguish failure while reading a stale wrapper from
failure inside destruction. It does not establish a general vendor bug. At the
start of this failed experiment the session held only the task-owned synthetic
sentinel. No unrelated scientific document was present. Execution stopped; Mnova
was not restarted and no alternative destruction sequence was attempted.

**Decision:** do not expose a native mutation backend. The Python API lacks an
accepted exact-destruction path in this investigation; the thin JS candidate has
failed. A reviewed lifecycle fix or an independently verified isolation route is
required before repeating save/reopen acceptance. An actual dirty sentinel is a
separate remaining requirement. Metadata success must not enable native writes.

## Current packaged probe protocol

`mnova_adapter/native_probe.py` contains only read-only metadata operations. It
locates the acceptance mailbox relative to its own package source:
`<repository>/.local/native/request.json`. A request has exactly these fields:

```json
{"schema_version": 1, "request_id": "probe-example-1", "operation": "probe"}
```

The identifier is ASCII alphanumeric with optional hyphens, maximum 80 characters.
All other operations are rejected before native calls. The script atomically
replaces `<request_id>.started.json` and `<request_id>.receipt.json` with JSON
records. Existing started/receipt records prevent automatic rerun of that ID.
Receipts include request identity, operation, timestamps, scope, state and result
or bounded error information. Raw receipts remain private.

This is a serial, single-owner acceptance harness. It is not a supported runtime
transport: atomic write replacement is not a multi-process lock, and its mailbox
does not provide production ACL, stale-job recovery or installation discovery.
Invocation exit alone is not acceptance. A started job without a matching final
receipt has an unknown completion outcome and must not be blindly retried.

Repeated invocation did not depend on changing environment variables: the
packaged script read the fixed mailbox inside the already-running process. A
future runtime needs a per-user mailbox, global writer ownership, request/receipt
identity validation and an explicit lifecycle gate. Do not use `-w`, single-instance
forwarding or a second launcher PID as proof of a separate native session.

## Static checks and remaining acceptance

The final read-only probe is subject to repository Python compilation and lint
checks. These checks do not repeat the native probe and cannot repair or accept
the failed lifecycle route. The experimental source is private, disabled and
identified by SHA-256 in the public evidence record.

Outstanding native gates: safe lifetime/ownership, actual dirty-document
preservation, processing and integration, native save, complete release, fresh
disk reopen with semantic/data equality, PDF/PNG/CSV exports, visual inspection,
and licence/module-specific behavior. Host transport, model behavior, artifact
delivery, scientific holdouts and release acceptance remain separate.

The subsequent [technical route review](NEXT_TECHNICAL_ROUTE.md) identifies a
possible stale cross-language wrapper and proposes a session-owned, Python-only
experiment. That review used documents and prior evidence only; no new native
execution or repair acceptance supersedes the failure recorded here.
