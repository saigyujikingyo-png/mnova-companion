# Implementation and acceptance status

Updated: 2026-09-16. Shared baseline: 2026-09-14.1.

| Area | State | Evidence |
| --- | --- | --- |
| Approved architecture | READY | User approved implementation after the Chembridge design review. |
| Native feasibility | R0 PARTIAL / R1 NOT RUN | Zero-page canvas access is guarded; session creation, UUID, owned synthetic content and separate readback succeeded. Existing-document activation returned without changing the UI or either active-document observation. Genuine dirty-edit and close gates remain blocked. Shipped mutations and public dispatch are disabled. See [current diagnostic](SESSION_DIAGNOSTIC_20260916.md); the [original R0 failure](SESSION_LIFECYCLE_R0.md) and earlier standalone failure remain historical evidence. |
| Core and output contracts | PORTABLE CHECKS PASS | Six typed MCP tool surfaces, input staging/artifact integrity and durable jobs. Native operations remain gated, so the planned interface is not complete. |
| Public repository | CREATED | Independent public repository created; implementation is a development preview. |
| Cloud environment | READY / PORTABLE SCOPE | Exact 9effac3 code checkout passed actual container setup, 171 tests plus 42 subtests (four platform skips), all portable checks and maintenance. Saved commands restored and read back. See [cloud evidence](CLOUD_SETUP.md); native/model/host delivery remain separate. |
| Current-device Codex installation | READY / BOUNDED | Icon, enabled personal plugin and non-editable private runtime verified; six installed MCP calls passed outside the checkout. See [installation](INSTALLATION.md). No host-model acceptance is inferred. |
| General installer, other hosts and delivery | UNVERIFIED | Standalone packaging, new-device/update/removal and actual host attachments remain unverified. No acceptance inherited from another product. |

Work order: native bootstrap and owned-document feasibility, core/contracts, 1D workflow, packaging/local host, remote hosts, benchmarks and scoped release. If a native gate cannot pass, record the observed limitation without claiming the workflow works.

## Current next step

Establish a supported owned document-window creation/activation route that preserves the existing inventory. The [current diagnostic](SESSION_DIAGNOSTIC_20260916.md) narrows the original snapshot failure and records the no-op activation. Do not repeat that setter or re-register an existing document without a supported ownership contract. A genuine dirty edit and independent readback remain prerequisites for R1. R2 save/reopen is not accepted.

No general installer, hosted relay, real host-model test or end-user release is claimed. This checkpoint provides portable infrastructure, a bounded current-device installation and explicit native-failure evidence.

The user approved R0/R1 implementation and continuation. The harness and diagnostic repairs are implemented; [R0 remains partial](NEXT_TECHNICAL_ROUTE.md). No native lifetime acceptance is inferred from the successful synthetic readback.

## Portable verification for this checkpoint

Local Windows checks passed: Ruff lint/format (21 files), **228 tests and 42
subtests passed**, with one symlink-privilege skip. Lifecycle guards account for
156 cases; execution-context and metadata-probe checks account for 14 and 10.
Six contract schemas (19,898 UTF-8
bytes) and actual MCP stdio structured/text parity and error branches passed.
These checks cover the disabled harness and portable core; they do not pass the
remaining native gates. No runtime wheel source changed in this phase.
