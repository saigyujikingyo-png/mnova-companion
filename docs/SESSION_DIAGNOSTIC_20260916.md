# Zero-page session diagnostic and recovery checkpoint

Date: 2026-09-16. Native build: **17.0.1-41952**, embedded Python **3.11.15**.
Current scope: developer acceptance only. Public native writes remain disabled.

This checkpoint follows the [original R0 failure](SESSION_LIFECYCLE_R0.md).
Its historical receipt and uncertain intent remain unchanged. The earlier
standalone/retained-JavaScript cleanup failure is a separate rejected route.

## Mechanism and evidence

An existing crash dump was inspected locally without generating or uploading a
dump. It records a read access violation, `0xC0000005`, at address `0x30`.
Matching installed import/export structures and captured code identify
`QtCanvas::allItems()` with a null receiver. A static binding-registration chain
and the Python attribute-read stack point to `Document.activeItem`.
This bounded local analysis did not independently prove the document's page count
and is not an independently verified debugger backtrace.

A new single-creation diagnostic separately persisted creation return, UUID read,
page count and function-scope return. All completed; the new document had **zero
pages**. No page/item/selection getter was used after that creation. Together,
these observations support guarding the first post-creation snapshot against a
missing canvas. They do not establish general binding ownership or repair the
earlier cross-language destruction experiment.

Both the lifecycle snapshot and metadata inventory now read `pageCount` first.
For zero pages they skip canvas access and report unavailable values as `null`
with `page_observation: "not_run_no_pages"`. Unknown counts cannot authorize a
close. The lifecycle harness also requires a completed matching target-creation
receipt before resolving a target for closure.

## Execution context and native checks

The new read-only `execution_context.py` binds the observed process ID, creation
FILETIME and window owner. The script thread matched the externally observed
main-window thread for this invocation. This does not prove a vendor threading
contract, absence of reentrancy, or ownership semantics; a window identity is
supplied from the current desktop observation rather than discovered by the probe.

| Check | Result |
| --- | --- |
| Creation, UUID and scope return without canvas access | Passed; zero pages observed |
| Independent zero-page snapshot | Passed |
| Owned synthetic spectrum creation | Passed; one page, one 16,384-point 1H spectrum at 400 MHz |
| Separate post-scope sentinel readback | Passed; identical snapshot and scientific-content hash |
| Unrelated startup document and diagnostic document | Preserved through these checks |
| Existing-document activation | Setter returned; independent readback was unchanged and the UI still displayed only the startup document |
| Genuine unsaved modification | Blocked by absent owned document view; content attachment alone returned `isModified=false` |
| Target close and separate post-close readback | Not run |
| Save, fresh disk reopen, scientific processing and export | Not run |

The original two-singlet synthetic fixture remains private. No user scientific
input, machine/process/document identifiers, proprietary images or licence data
are included in public evidence. The accepted readback concerns native in-memory
data, not a saved or delivered file.

The activation diagnostic assigned `Framework.instance.activeDocument` once to
the uniquely resolved owned document. It did not create, register or close any
document. The complete function returned, but both native observers still
identified the startup document and the full snapshot digest was unchanged.
This is an observed no-op, not an accepted activation route. No edit action was
sent to the startup document. The claim remains retained and is not replayed.

`Framework.addDocument` explicitly adds a document to the main window's handled
list. Its installed examples concern standalone documents. Neither those
examples nor its documentation specify duplicate-registration or blank-document
replacement behavior for an existing session document, so it was not called.
Session membership and a usable document view require separate evidence.

The next native investigation must establish an owned document window through
a documented main-window creation route, with explicit preservation of the
existing inventory. A bounded `action_File_New` callback is a candidate requiring
its own creation/identity/view checks. Do not repeat the completed setter or use
`lockDocument` to imitate visible document activation. Only after a genuine dirty
edit and independent readback may the R1 close experiment proceed. The disposable
target must have an observed page and zero items before the close guard permits it.

## Remaining boundary

`MUTATIONS_ENABLED=False` remains the shipped default, and the production MCP
dispatcher is unchanged. A private process-bound experiment runner enabled only
the reviewed local acceptance calls. None of these adapters is shipped in the
installed runtime wheel. R1 requires a genuinely dirty protected sentinel and an
observably clean owned target; unavailable page/item state is not a clean target.

Portable tests, GitHub CI, the Codex cloud environment, native execution, installed
host/model behavior and file delivery remain independent evidence.

Local verification on this code: Ruff lint/format (21 files), **228 tests and
42 subtests passed**, one Windows symlink-privilege skip, six output contracts
(19,898 UTF-8 schema bytes), and actual MCP stdio structured/text/error checks.
The focused zero-page checks failed against the old access paths before the fix.
These results validate guards, not the missing document-view or R1 lifecycle gate.

See the [sanitized receipt](../acceptance/session_diagnostic_20260916.json).
