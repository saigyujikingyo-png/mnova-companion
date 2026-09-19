# P0 portable execution boundary

Date: 2026-09-16. Scope: owner-approved C3/P0 implementation using fake execution.
This does not implement an Mnova executor, enable scientific writes or accept
the failed native lifecycle. The public interface remains six tools, version 1.0.

## Behavior

`execution.py` defines bounded JSON contracts for build profiles, handshakes,
attempt identities, dispatch, phase receipts and materialized evidence files.
Only `portable_fake` profiles are admitted. Diagnostic/native profiles can be
represented for future qualification but are always rejected by P0 admission.
No native adapter is loaded and no arbitrary-script tool is exposed.

`jobs.py` retains request-key idempotency and the OS-held metadata lock. New
version-2 records bind attempts to session, process-instance identity, fencing
token, build, operation, document revision and phase sequence. Fake identities
exercise matching; they do not prove real native process identity or isolation.

| Internal operation | Contract |
| --- | --- |
| prepare_job | Validate fake profile/handshake, request and deadline; publish exclusive lease and prepared job. No effect execution. |
| dispatch_once | Recheck identity, payload, quarantine, deadline and revision; durably consume before permission to run one fake effect. Repeated consumption returns false. |
| record_receipt | Require ordered return, observation, scope-release and post-scope receipts. Exact JSON duplicates are idempotent; conflicts are retained and quarantined. |
| complete | Require the full consistent chain, known effects and completed cleanup. Unknown/quarantined attempts cannot use this path; earlier failure cannot become final success. |
| mark_unknown | Retain lease and past-effect quarantine; schedule no retry. |
| reconcile_verified | Require current revision and matching, hash-verified fake evidence for the full phase chain. Resolve effects without releasing the executor lease or restoring its usability. |
| retire_executor | Require a matching fake retirement witness and retain its file/hash reference; release only the matching resource lease, never past-effect quarantine. |

P0 witness files are trusted fake-supervisor inputs, not cryptographic attestation
or evidence of vendor behavior. They cannot be submitted through public MCP
arguments. Their contents bind the exact attempt and the receipt digest or a
witnessed stopped executor. Files must reside inside the evidence directory and
match bounded length and SHA-256. This fake verifier must not be promoted to a
native acceptance authority.

## Failure and persistence rules

- Job records are authoritative for past effects; native.lock controls a resource.
  Removing or retiring the resource cannot erase unknown effects.
- Unresolved jobs block new dispatch across new keys, sessions and restarts.
  A resolved unknown executor still needs retirement; its old session is unusable.
- A consumed attempt is never automatically dispatched twice, including failure
  after durable intent but before an effect. This is not exactly-once execution.
- Journaling and execution are not one transaction. Interrupted prepared/consumed
  jobs stay blocked; a supervisor can mark a matching active attempt unknown.
  Store construction never infers recovery or drains the queue.
- Interruption between lease creation and job publication leaves a queued job
  with a lease. It cannot be retried or silently unlocked; cancellation records
  unknown for isolated review. Malformed and legacy leases are never stolen.
- Interruption after a confirmed terminal record but before lease deletion can
  be repaired by the matching completion/dispatch acknowledgement, without running
  an effect again or deleting another attempt's lease.
- Unconsumed cancellation is acknowledged before execution. After consumption it
  remains requested until supported completion/reconciliation; there is no close,
  process kill or claim of no effect.
- Fsynced atomic files and process-crash tests are not a universal power-loss
  durability guarantee. Journals are local-only; network/cloud-synced state and
  concurrent external editing are unsupported.

There is no background queue worker, timeout monitor, relaunch, lease TTL or
dead-PID cleanup. A test fake receiver uses a separate Python subprocess and the
real journal; its parent verifies that a consumed effect cannot repeat after
process exit. This is not native process-boundary acceptance. Production IPC
authentication and executor launch/identity validation belong to later integration.

## Compatibility and limits

Historical records without new fields remain readable without rewriting bytes
when their requests satisfy the P0 wire bounds: 128 KiB encoded size, depth 16,
10,000 nodes and signed 64-bit integers. The older reader accepted requests
outside these bounds; the new reader rejects those records conservatively and
leaves their files intact. Preserve the old reader and originals for separate
review; rejection is not permission to erase, recreate or replay a job.
Old active/unknown records and leases are unfenced: no attempt identity is
invented and no completion permission inferred. Historical terminal results gain
no native verification. New records are incompatible with the older strict reader;
use separate state for an older runtime during rollback. The original P0 source checkpoint did not upgrade the installed runtime.
The dev2 [installation procedure](INSTALLATION.md) requires separate runtime
and state identities, a fresh inventory and independently verified package bytes.

Internal claim, arbitrary phase and complete(job_id, dict) APIs were replaced
with typed preparation/receipts/completion. They had no enabled native production
caller. Public schemas are unchanged. mnova_job now reports unknown effects for
running, cancel-requested, interrupted, unknown and conflicting-record cases.
Public reconcile remains read-only and cannot accept client success assertions.

Messages accept bounded finite independent JSON values. Wrappers, buffer views,
exception objects and custom encoders are rejected before encoding. A phase chain
is hashed as four bounded message digests, so a valid aggregate cannot exceed the
single-message limit during reconciliation. JSON boolean/integer differences
remain meaningful when matching late receipts.

## Verification and next gate

Tests cover profile rejection, identity/fencing, competing consumers, subprocess
exit, every phase interruption, late/conflicting receipts, cancellations, new-key
and new-session quarantine, legacy records, failed journal publication, terminal
publication/unlink interruptions and JSON/file limits. The full README checks
must pass on the integrated working tree; see current results in STATUS.md.

Native mutations and target close remain disabled. P1 requires an accepted
isolated diagnostic environment and supported bootstrap/runtime/observer contracts.
Save/reopen/editability, science, host delivery, installer, cloud/CI and release
remain independent gates. P0 does not repair or reproduce native incidents S/F/A.
