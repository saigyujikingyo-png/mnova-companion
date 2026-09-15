# Implementation and acceptance status

Updated: 2026-09-15. Shared baseline: 2026-09-14.1.

| Area | State | Evidence |
| --- | --- | --- |
| Approved architecture | READY | User approved implementation after the Chembridge design review. |
| Native feasibility | PARTIAL / FAILED LIFECYCLE GATE | Python trigger and readback observed. A guarded cross-engine standalone-document destruction test crashed Mnova with c0000409. Native mutation dispatch is disabled; save/reopen/export not accepted. See [native investigation](NATIVE_API.md) and [bounded receipt](../acceptance/native_20260915.json). |
| Core and output contracts | PORTABLE CHECKS PASS | Six typed MCP tool surfaces, input staging/artifact integrity and durable jobs. Native operations remain gated, so the planned interface is not complete. |
| Public repository | CREATED | Independent public repository created; implementation is a development preview. |
| Cloud environment | READY / PORTABLE SCOPE | Original access restored; exact e861d52 core checkout passed actual container setup, maintenance and portable checks. See [cloud evidence](CLOUD_SETUP.md); native/model/host delivery remain separate. |
| Current-device Codex installation | READY / BOUNDED | Icon, enabled personal plugin and non-editable private runtime verified; six installed MCP calls passed outside the checkout. See [installation](INSTALLATION.md). No host-model acceptance is inferred. |
| General installer, other hosts and delivery | UNVERIFIED | Standalone packaging, new-device/update/removal and actual host attachments remain unverified. No acceptance inherited from another product. |

Work order: native bootstrap and owned-document feasibility, core/contracts, 1D workflow, packaging/local host, remote hosts, benchmarks and scoped release. If a native gate cannot pass, record the observed limitation without claiming the workflow works.

## Current next step

Investigate a supported document-lifecycle route that avoids the failing cross-engine handle destruction. First obtain a concrete ownership/release explanation from current vendor documentation or a separately authorised vendor support exchange; do not repeat the known crash. Preserve the original experiment and event evidence privately. Once a safe route exists, rerun the owned/unsaved-session gate before enabling any native write or attempting save/reopen/export acceptance.

No general installer, hosted relay, real host-model test or end-user release is claimed. This checkpoint provides portable infrastructure, a bounded current-device installation and explicit native-failure evidence.

The [next technical route](NEXT_TECHNICAL_ROUTE.md) proposes a pure-Python session-owned lifetime experiment after genuine dirty-sentinel and close-semantics preconditions. It is a plan only. The current turn stops before that native implementation.
