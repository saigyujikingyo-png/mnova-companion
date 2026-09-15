# Implementation and acceptance status

Updated: 2026-09-15. Shared baseline: 2026-09-14.1.

| Area | State | Evidence |
| --- | --- | --- |
| Approved architecture | READY | User approved implementation after the Chembridge design review. |
| Native feasibility | PARTIAL / FAILED LIFECYCLE GATE | Python trigger and readback observed. A guarded cross-engine standalone-document destruction test crashed Mnova with c0000409. Native mutation dispatch is disabled; save/reopen/export not accepted. |
| Core and output contracts | PORTABLE CHECKS PASS | Six typed MCP tool surfaces, input staging/artifact integrity and durable jobs. Native operations remain gated, so the planned interface is not complete. |
| Public repository | CREATED | Independent public repository created; implementation is a development preview. |
| Cloud environment | CREATED; CHECKS SEPARATE | Saved and selector-verified; see CLOUD_SETUP.md for actual checked revision and results. |
| Installer, hosts and delivery | UNVERIFIED | No acceptance inherited from another product. |

Work order: native bootstrap and owned-document feasibility, core/contracts, 1D workflow, packaging/local host, remote hosts, benchmarks and scoped release. If a native gate cannot pass, record the observed limitation without claiming the workflow works.

## Current next step

Investigate a supported document-lifecycle route that avoids the failing cross-engine handle destruction. First obtain a concrete ownership/release explanation from current vendor documentation or a separately authorised vendor support exchange; do not repeat the known crash. Preserve the original experiment and event evidence privately. Once a safe route exists, rerun the owned/unsaved-session gate before enabling any native write or attempting save/reopen/export acceptance.

No installer, hosted relay, real host-model test or end-user release is claimed. This checkpoint provides portable infrastructure and explicit native-failure evidence.
