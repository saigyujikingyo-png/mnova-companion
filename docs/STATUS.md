# Implementation and acceptance status

Updated: 2026-09-16. Shared baseline: 2026-09-14.1.

| Area | State | Evidence |
| --- | --- | --- |
| Approved architecture | C3 / P0 APPROVED | Owner confirmed the dedicated-executor direction and limited the first code increment to portable jobs, receipts and recovery. See [P0 boundary](P0_EXECUTION.md). |
| Current interface research | PARTIAL / NATIVE GATES CLOSED | Existing F dump analysis identified a purecall/abort termination path without identifying the originating object or explaining S. Ownership, exact close/window and isolation contracts remain incomplete; vendor consultation remains parallel evidence. |
| C3/P0 execution boundary | READY / LOCAL PORTABLE CHECKS PASS | Typed fake dispatch, attempt/session fencing, phase receipts, independent unknown reconciliation and persistent effect quarantine. No Mnova executor or public native write enabled. |
| I0 diagnostic environment | WINDOWS INSTALLING; ACCEPTANCE OPEN | VMP/WHP enabled after owner restart; official evaluation ISO hash verified; NEM/WHP VM runtime and disabled network/shares read back. Owner accepted licence terms; installation is progressing on the new 80 GiB VDI. First-boot setup, rollback and final baseline remain unaccepted. See [I0 preparation](I0_ENVIRONMENT.md). |
| Native feasibility | R0 PASSED BOUNDED / R1 FAILED | Main-window ownership and genuine dirty state passed separate readback. The target-close sequence then removed the protected synthetic sentinel while retaining its target. Independent reconciliation confirmed the failure and preserved original document state. All writes stopped; a separate close gate is disabled. See [current lifecycle record](SESSION_LIFECYCLE_R1.md). |
| Core and output contracts | PORTABLE CHECKS PASS | Six typed MCP tool surfaces, input staging/artifact integrity and durable jobs. Native operations remain gated, so the planned interface is not complete. |
| Public repository | CREATED | Independent public repository created; implementation is a development preview. |
| Cloud environment | READY / PORTABLE SCOPE | Exact 77f6dac code checkout passed actual container setup, 270 tests plus 42 subtests (four platform skips), all portable checks and maintenance. Saved commands restored and read back. See [cloud evidence](CLOUD_SETUP.md); native/model/host delivery remain separate. |
| Current-device Codex installation | READY / BOUNDED | Icon, enabled personal plugin and non-editable private runtime verified; six installed MCP calls passed outside the checkout. See [installation](INSTALLATION.md). No host-model acceptance is inferred. |
| General installer, other hosts and delivery | UNVERIFIED | Standalone packaging, new-device/update/removal and actual host attachments remain unverified. No acceptance inherited from another product. |

Work order: native bootstrap and owned-document feasibility, core/contracts, 1D workflow, packaging/local host, remote hosts, benchmarks and scoped release. If a native gate cannot pass, record the observed limitation without claiming the workflow works.

## Current next step

The owner-approved [P0 portable boundary](P0_EXECUTION.md) is complete in the local
working tree. The owner subsequently authorized [I0 preparation](I0_ENVIRONMENT.md)
and selected a local VM. Host restart, official evaluation ISO integrity and
bounded VM startup are verified. Owner licence acceptance and the guest
installation-progress screen were observed. Complete installation and applicable
owner first-boot steps, then accept actual
isolation/rollback and the final software baseline before P1. I0 remains open.
C3 supersedes the earlier C1 next-step proposal. Evaluate any vendor
reply against the [interface matrix](INTERFACE_CONTRACT_REVIEW.md) in parallel;
this turn did not check for a new reply. Preserve the failed receipt; do not replay
the target-close sequence or clean up its remaining target. R2 save/reopen remains
blocked. P0 approval does not authorize native experiments or write enablement.

No general installer, hosted relay, real host-model test or end-user release is claimed. This checkpoint provides portable infrastructure, a bounded current-device installation and explicit native-failure evidence.

The user approved R0/R1 implementation and continuation. Main-window R0 is accepted only within the [recorded bounded experiment](SESSION_LIFECYCLE_R1.md). R1 failed despite passing its clean target-creation prerequisite. The removed sentinel was task-generated synthetic data; no user scientific file was an experiment input. Portable failure containment does not repair native closure.

## Current P0 portable verification

The integrated local working tree passed **341 tests and 42 subtests**, with two
skips because this Windows token cannot create the symbolic-link fixtures. Ruff
lint/format passed for 24 Python files. Six public tool schemas remain 19,898
UTF-8 bytes; six internal P0 schemas were also validated. Actual MCP stdio checks
passed with six tools, structured/text parity and error branches. Tracked-source
release preflight passed; new files received a separate source/privacy check.

The initial late-receipt gap was reproduced using only temporary fake records.
Independent review also found a JSON boolean/integer duplicate-comparison defect;
its two regression cases failed before the fix and passed afterward. Real process
exit, interrupted journal publication and lease cleanup tests remain portable
fake evidence, not tests of Mnova. See [P0 contracts and limits](P0_EXECUTION.md)
and the [source/check receipt](../acceptance/p0_portable_20260916.json).

Native adapter source and its two disabled gates are unchanged. No native
experiment, cloud/remote CI rerun, package installation, Git publication, release
or installed-host upgrade was performed for P0. Existing cloud and installation
receipts below remain historical at their recorded revisions.

## Historical portable verification before P0

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
