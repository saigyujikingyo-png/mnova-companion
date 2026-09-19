# Contract and operation coverage

Contract version: 1.0. Package: 0.1.0.dev1. Public outputs are generated from shared typed definitions, validated in the service and emitted as structuredContent plus consistent JSON text. Media bytes are separate MCP content blocks.

| Tool / operation | Implemented and tested | Remaining acceptance |
| --- | --- | --- |
| mnova_status | Registration/file versions have distinct provenance; unknown licence; explicit unavailable native state | Live native licence/module capabilities |
| mnova_help | Compact discovery and per-tool input/output schemas | Detailed schemas for future native operations |
| mnova_open | Owner-selected input roots, bounded copy, manifest/hash, explicit native_import_state=not_run | Actual native import and document/revision handling |
| mnova_run | Known request schema; gated operations return CAPABILITY_UNVERIFIED before jobs/native side effects | Every scientific native operation and its detailed schema |
| mnova_job read/cancel | Versioned durable records; uncertain active effects remain unknown; cancelled-before-entry versus cancel-requested; malformed record error with known job ID | Integrated native interruption/cancellation |
| mnova_job reconcile | Observation of stored state; never clears an unknown native lease or replays | Native receipt/artifact reconciliation; full reconcile operation is pending |
| mnova_artifacts list/read/preview | Bounded registry, metadata, original bytes with hash check; PNG/JPEG media route | Native artifact provenance, exporter acceptance and receiving-host delivery |

Tests cover invalid inputs, malformed outputs, unknown jobs, missing/unsupported native operations, unavailable quantities versus zero, finite numbers, text/structured parity and hash failures. Artifact-store tests cover raw-directory staging, byte/file limits, traversal, reparse points, metadata tampering and restart readback. The job tests cover repeated and conflicting requests, one native lease, cancellation, crash-released metadata locks and retained unknown native outcomes.

The six tools are not a declaration that the complete planned interface is implemented. Protocol success, portable data integrity, scientific correctness, native editability and host delivery remain independent evidence.

The [P0 execution boundary](P0_EXECUTION.md) adds six internal strict schemas,
without adding public tools or enabling native operations. Tests exercise fake
profile gates, fenced one-time dispatch, phase-chain completion, quarantine across
restart/retirement, verified fake reconciliation, file/JSON bounds and interruption
windows. Public reconcile remains read-only. Fake witnesses are not native
verification or client-authorized recovery.

The current inline binary route is limited to 16 MiB and table pages to 50 entries. Larger artifact delivery and destination adapters are pending. No installed-host or Terra max model benchmark has run.
