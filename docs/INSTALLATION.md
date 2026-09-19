# Current-device Codex preview installation

Source version `0.1.0.dev2` is a developer-assisted portable preview. It includes
fake-only P0 dispatch and job persistence. Native scientific writes and target
close remain disabled; this is not a general installer or a native NMR release.
An installed version requires its own package/configuration receipt.

## Runtime and plugin identity

The personal Codex plugin is `mnova-companion@personal`. Its original icon is in
[assets](../assets/DESIGN.md). The private MCP configuration starts a non-editable
Python environment with `python -I -m mnova_companion`; it does not import the
checkout. The plugin source is under the user's `plugins/mnova-companion`, with a
separate host-managed cache. Only that private source adds the concrete
`.mcp.json` reference and machine-specific runtime/home paths.

The environment uses an existing Python 3.12 base and locked production
dependencies. It still depends on that Python base and cannot be copied as a
self-contained installation to a different device. Input roots default to `[]`.
Status, help, authorized staging and registered artifacts are portable; native
requests return an unavailable-capability result before creating a job.

## Upgrade admission and preservation

1. Freeze a tested source revision and build its wheel/sdist. Record their hashes
   and check the installed source against the exact wheel, including `execution.py`.
2. Preserve old plugin source/configuration, runtime, jobs, keys, leases, artifacts
   and evidence. Inventory canonical old and new homes, including hidden files and
   reparse points. Never let old and new readers share a state directory.
3. A fresh empty versioned home is admitted only if a fresh, complete inventory
   finds no old state/artifact files, unresolved attempts, leases or quarantine.
   Existing records require a separate compatibility/migration review; do not use
   an empty new home to hide unknown effects. Recheck immediately before switching.
4. Install the wheel in a new versioned runtime such as
   `%LOCALAPPDATA%/MnovaCompanion/runtimes/0.1.0.dev2`. Explicitly configure a distinct
   home such as `%LOCALAPPDATA%/MnovaCompanion/profiles/0.1.0.dev2`. The server's
   default home is not a migration mechanism. Keep the old runtime/home intact.
5. Run installed protocol checks from outside the checkout using temporary
   synthetic fixtures. Verify new/old canonical homes differ and all native gates
   remain closed. This preview provides no automatic runtime migration or host
   frontend shutdown mechanism.

P0 version-2 records cannot be read by the older strict reader. Historical records
are readable by dev2 only within the P0 wire bounds described in
[P0_EXECUTION.md](P0_EXECUTION.md). Over-limit legacy records are conservatively
rejected without rewriting their files. Retain originals and the old reader for
review; rejection never authorizes deletion, re-submission or invented completion.

## Official plugin switch and verification

After package verification and admission, update the existing local plugin source
and its private connection configuration. Use the official plugin-creator
cachebuster helper, validate the source, then run
`codex plugin add mnova-companion@personal`. This reinstalls the plugin integration;
it does not itself replace a wheel. Do not edit host cache or registration internals.
Preserve the existing marketplace name, source path, order and unrelated plugins.

Re-read the installed cache manifest/configuration and invoke its exact command in
a fresh stdio client. Check discovery, output schemas, structured/text parity and
expected error branches for all six tools. Existing host-owned frontends may retain
the old runtime; do not close Codex or native software to force replacement.
Start a new Codex task for host/model acceptance. Direct installed protocol is
separate from current-task hot reload, a model workflow or received attachments.

## Rollback and removal

Rollback uses the retained old runtime **and its old compatible home**, through the
same official plugin reinstall flow. Preserve the new home and evidence as well.
New unknown effects must still block subsequent work across rollback; do not feed
version-2 files to the older reader or restore an old snapshot to erase them.
A synthetic isolated rollback check proves path/reader separation, not recovery of
an in-flight native operation. Whole-host, OS-event and clean-device rollback
acceptance remain open.

Codex plugin removal removes host integration; separate runtime/state cleanup
requires its own explicit scope. No user data or native sessions are removed by
this upgrade procedure. Removal/reinstallation after removal is untested.

## Historical dev1 installation

The [2026-09-15 receipt](../acceptance/installation_20260915.json) records the older
`0.1.0.dev1` current-device installation and six-tool protocol checks. At that
inspection, its private runtime held 45,991,717 bytes in 2,010 files, excluding the
shared Python base, host cache and icon. These are historical values, not dev2
package size or acceptance. The CLI resolved `./plugins/mnova-companion` from the
user home; preserving that source location avoided marketplace rewrites.
