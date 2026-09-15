# Implementation and acceptance status

Updated: 2026-09-15. Shared baseline: 2026-09-14.1.

| Area | State | Evidence |
| --- | --- | --- |
| Approved architecture | READY | User approved implementation after the Chembridge design review. |
| Native feasibility | R0 FAILED / R1 NOT RUN | New session-lifecycle harness and exact-snapshot preflight ran; Mnova crashed before sentinel ownership was established. No dirty edit or target close ran. Acceptance mutations and production dispatch are disabled. See [R0 result](SESSION_LIFECYCLE_R0.md). The earlier [standalone failure](../acceptance/native_20260915.json) is separate evidence. |
| Core and output contracts | PORTABLE CHECKS PASS | Six typed MCP tool surfaces, input staging/artifact integrity and durable jobs. Native operations remain gated, so the planned interface is not complete. |
| Public repository | CREATED | Independent public repository created; implementation is a development preview. |
| Cloud environment | READY / PORTABLE SCOPE | Original access restored; exact e861d52 core checkout passed actual container setup, maintenance and portable checks. See [cloud evidence](CLOUD_SETUP.md); native/model/host delivery remain separate. |
| Current-device Codex installation | READY / BOUNDED | Icon, enabled personal plugin and non-editable private runtime verified; six installed MCP calls passed outside the checkout. See [installation](INSTALLATION.md). No host-model acceptance is inferred. |
| General installer, other hosts and delivery | UNVERIFIED | Standalone packaging, new-device/update/removal and actual host attachments remain unverified. No acceptance inherited from another product. |

Work order: native bootstrap and owned-document feasibility, core/contracts, 1D workflow, packaging/local host, remote hosts, benchmarks and scoped release. If a native gate cannot pass, record the observed limitation without claiming the workflow works.

## Current next step

Resolve the session-creation execution-context and ownership contract before another native mutation. The new failure interval includes creation, its returned UUID read and the first post-create snapshot; the exact faulting instruction is unknown. The [R0 decision record](SESSION_LIFECYCLE_R0.md) defines narrower checkpoints and preserves the no-replay boundary. No target close or R2 save/reopen experiment is justified by the current evidence.

No general installer, hosted relay, real host-model test or end-user release is claimed. This checkpoint provides portable infrastructure, a bounded current-device installation and explicit native-failure evidence.

The user approved R0/R1 implementation. Its acceptance harness is implemented, but the first mutation failed at R0. The [next technical route](NEXT_TECHNICAL_ROUTE.md) now records this checkpoint; it does not claim a repaired native lifecycle.

## Portable verification for this checkpoint

Local Windows checks passed: Ruff lint/format (19 files), **174 tests and 42
subtests passed**, with one symlink-privilege skip. The new acceptance-harness
guard tests account for 119 passing cases. Six contract schemas (19,898 UTF-8
bytes) and actual MCP stdio structured/text parity and error branches passed.
These checks cover the disabled harness and portable core; they do not make the
failed native experiment pass. No runtime wheel source changed in this phase.
