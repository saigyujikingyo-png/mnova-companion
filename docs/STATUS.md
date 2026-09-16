# Implementation and acceptance status

Updated: 2026-09-16. Shared baseline: 2026-09-14.1.

| Area | State | Evidence |
| --- | --- | --- |
| Approved architecture | READY | User approved implementation after the Chembridge design review. |
| Native feasibility | R0 PASSED BOUNDED / R1 FAILED | Main-window ownership and genuine dirty state passed separate readback. The target-close sequence then removed the protected synthetic sentinel while retaining its target. Independent reconciliation confirmed the failure and preserved original document state. All writes stopped; a separate close gate is disabled. See [current lifecycle record](SESSION_LIFECYCLE_R1.md). |
| Core and output contracts | PORTABLE CHECKS PASS | Six typed MCP tool surfaces, input staging/artifact integrity and durable jobs. Native operations remain gated, so the planned interface is not complete. |
| Public repository | CREATED | Independent public repository created; implementation is a development preview. |
| Cloud environment | READY / PORTABLE SCOPE | Exact 77f6dac code checkout passed actual container setup, 270 tests plus 42 subtests (four platform skips), all portable checks and maintenance. Saved commands restored and read back. See [cloud evidence](CLOUD_SETUP.md); native/model/host delivery remain separate. |
| Current-device Codex installation | READY / BOUNDED | Icon, enabled personal plugin and non-editable private runtime verified; six installed MCP calls passed outside the checkout. See [installation](INSTALLATION.md). No host-model acceptance is inferred. |
| General installer, other hosts and delivery | UNVERIFIED | Standalone packaging, new-device/update/removal and actual host attachments remain unverified. No acceptance inherited from another product. |

Work order: native bootstrap and owned-document feasibility, core/contracts, 1D workflow, packaging/local host, remote hosts, benchmarks and scoped release. If a native gate cannot pass, record the observed limitation without claiming the workflow works.

## Current next step

Resolve the relationship between session documents, GUI document windows, wrapper ownership and exact-target closure before selecting another isolated experiment. Preserve the failed receipt and do not replay the target-close sequence or automatically clean up the remaining target. R2 save/reopen is blocked.

No general installer, hosted relay, real host-model test or end-user release is claimed. This checkpoint provides portable infrastructure, a bounded current-device installation and explicit native-failure evidence.

The user approved R0/R1 implementation and continuation. Main-window R0 is accepted only within the [recorded bounded experiment](SESSION_LIFECYCLE_R1.md). R1 failed despite passing its clean target-creation prerequisite. The removed sentinel was task-generated synthetic data; no user scientific file was an experiment input. Portable failure containment does not repair native closure.

## Portable verification for this checkpoint

Local Windows checks passed: Ruff lint/format (21 files), **273 tests and 42
subtests passed**, with one symlink-privilege skip. Lifecycle guards account for
201 cases; execution-context and metadata-probe checks account for 14 and 10.
Six contract schemas (19,898 UTF-8
bytes) and actual MCP stdio structured/text parity and error branches passed.
These checks cover the disabled harness and portable core; they do not pass the
remaining native gates. No runtime wheel source changed in this phase.

For exact containment code revision `77f6dac`, [GitHub CI](https://github.com/saigyujikingyo-png/mnova-companion/actions/runs/35083634919)
passed on Windows (274 tests, 44 subtests) and Ubuntu (270 tests, four platform
skips, 42 subtests). This is separate from the actual Codex cloud-environment runs
recorded in `CLOUD_SETUP.md`.
