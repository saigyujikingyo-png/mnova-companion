# Session lifecycle R0 implementation and result

Date: 2026-09-15. State: **R0 FAILED; R1 NOT RUN**.

The user approved the next implementation phase after reviewing the technical
route. This checkpoint implemented its bounded R0/R1 acceptance harness and ran
R0 on the installed Windows build. It did not establish a native lifetime fix.

## Implemented boundaries

`mnova_adapter/session_lifecycle.py` is a developer acceptance harness, outside
the wheel and public MCP dispatcher. It uses Python session creation/closure and
a temporary synchronous JavaScript observer for the read-only dirty flag. It
never intentionally retains a JS document wrapper between calls.

- Fixed operation names and exact request fields; no supplied executable code.
- Private session/process and full snapshot binding before mutation.
- Current page, active item and selected page/item identities are observed along
  with inventory and the actual document dirty flag. Only owned fixtures permit
  scientific-content hashing. Ownership from a different process does not permit
  content reads even if a reopened document retains its UUID; unregistered
  documents remain metadata-only. This bounded process-ID fence is not a full
  production session identity and does not solve process-ID reuse.
- Exclusive, flushed request claims and per-operation intent files prevent
  replay under both the same and a different request ID.
- Ownership requires a newly returned UUID and exactly one inventory addition;
  an existing blank document must never become owned by inference.
- Target close requires a genuinely dirty, unchanged sentinel, matching active
  document observations and a clean owned target. A close is attempted once.
  No post-close old-wrapper read, JS destruction or automatic cleanup is used.
- Even an in-call success remains pending until a separate read-only invocation
  after the entire Python scope returns. Mocks cannot satisfy this native gate.

Following the observed R0 failure, **acceptance mutations are disabled by default
before native imports**, including well-formed requests. The existing public
`mnova_run` native gate remains closed. Historical operation code is retained for
review, not exposed as a working backend.

## What actually ran

Native build: 17.0.1-41952; embedded Python: 3.11.15.

1. Launched a fresh application session. Native UI and a successful read-only
   invocation observed one clean blank startup document, no page items and Undo
   enabled. Python and JS agreed on its active document identity.
2. Submitted one `create_sentinel` request bound to that exact snapshot. A second
   preflight read matched it. The durable `create_sentinel_intent` checkpoint was
   written at **2026-09-15 19:31:49 UTC**.
3. Mnova displayed **"Our apologies, MestReNova has crashed"** in its native
   **Oops!** dialog. The next `sentinel_created` checkpoint, ownership record and
   final receipt were absent. The process remained present at observation time;
   presence and responsiveness do not mean successful native execution.
4. No dirty-edit action, target creation, target close, native save, reopen or
   export was reached. No retry, force-close, crash-dump generation or support
   transmission was performed. Native writes stopped at the failed R0 gate.

The failure interval contains `newDocument(...)`, reading its returned UUID and
the first post-creation snapshot. The last checkpoint does **not** identify which
of these instructions faulted. The new observation is distinct from the earlier
standalone/retained-JS-handle destruction crash. It does not confirm that old
hypothesis or reuse its exception code. No new Windows exception code was
established while the application crash handler remained open.

The exact executed harness was frozen privately with SHA-256
`daf98cf683b0dbe2ebdbfe1dd7dc9692e593887152d89810341bfcbb88776d46`.
The public copy additionally disables mutations after this failure. Raw request
IDs, native identities, process IDs and local paths remain private. The public
[bounded receipt](../acceptance/session_lifecycle_r0_20260915.json) records only
the necessary result and provenance.

## Decision and next diagnostic route

R0 remains failed and R1 was not run. A genuine dirty sentinel, supported session
close and protection of unsaved work are still unverified. R2 and later scientific
features must not start from this result.

Before another native mutation, establish the execution-context contract for
`DocumentPlugin.newDocument`: which thread/event context accepts it, how the
returned binding is owned, and whether document replacement or a re-entrant
observer is allowed. The installed signature alone does not answer these points.
Inspect documented official examples and any owner-provided diagnostic evidence;
do not infer a fix from a renamed method or Python reference lifetime.

If that contract supplies a concrete safe route, the next experiment should
separate creation return, identity read, and fresh inventory into individual
checkpoints, with no post-create JS observer in the first creation probe. Preserve
the original blank-document inventory and all uncertain intents. Do not replay
this request or close an unproven target to clean up a failed experiment.

Read existing crash evidence before generating more. If a thread mismatch remains
a concrete hypothesis, a future read-only diagnostic can compare the script's OS
thread identity with the known application's GUI thread. Python's main-thread
label or a successful metadata call does not establish the GUI execution context.
An equal thread identity would still leave reentrancy and binding ownership open.

An isolated Console candidate remains conditional on verified invocation,
licensing and process isolation. No such isolation or entitlement is accepted.
Sending a vendor report is a separate external communication; no report was sent.

Portable regression results are recorded in `STATUS.md`. Current-device plugin
installation and the earlier cloud-core check retain their previously recorded
scope; this adapter is not included in the installed runtime wheel.
