# Native interface contract review

Date: 2026-09-16. Scope: documentation and retained-evidence analysis only.
Decision: **public references obtained; lifecycle contract still PARTIAL;
replacement native execution BLOCKED**. No implementation or native experiment
was performed during this review.

## 1. Sources and version boundaries

The installed reference belongs to Mnova **17.0.1-41952**, with embedded Python
**3.11.15**. The [current online manual](https://mestrelab.com/downloads/mnova/manuals/latest/)
identifies itself as **v17.0.0.3184c2c**. Its relevant Python method descriptions
agree with the installed reference, but the online manual is not proof of an
identical binding build. Links using `latest` may change after this review.

Local source fingerprints were read back on this date. Paths below are relative
to the Mnova installation. Vendor files are not copied into this repository.

| Installed source | SHA-256 |
| --- | --- |
| `documents/python/MnovaDocument.html` | `072b157aa06cd94049c2662587796c9dde5856a53ec0f51e8a79c175436fa98a` |
| `documents/python/MnovaFramework.html` | `48e92229c67ba2d3d940e0c4308dd891cf73b3c758de36d35c9b19517a2c070b` |
| `documents/python/MnovaNMR.html` | `4f99c56cd518fde710b15b1575b8817e1e090f2972e6bbbcd0569c543964f5d3` |
| `examples/scripts/py/createSpectrum.py` | `df4aaa537ce7f0df1b4e35fe9443e89946e888aa901da146bb0a89486b20c47e` |

## 2. Obtained descriptions and remaining gaps

Here, **task ownership** means recorded permission to act on a task-created
document. **Memory ownership** means responsibility for keeping or destroying a
native object. A task ownership receipt does not establish memory ownership.

| Interface | What the reviewed description establishes | What it does not establish |
| --- | --- | --- |
| [DocumentPlugin](https://mestrelab.com/downloads/mnova/manuals/latest/stubs/MnovaDocument.html#MnovaDocument.DocumentPlugin) | `newDocument` creates/adds a document; `documents` lists the session; `closeDocument` takes a Document and returns None. | A corresponding GUI window, memory ownership, cancellation, completion time, or alias invalidation. None is not a success signal. |
| Document / Page | Installed constructors describe an empty document or file path; pages and items have construction/access methods. | A UUID constructor, zero-page getter safety in general, parent retention or attachment transfer. The observed guard fixes only the diagnosed path. |
| [Framework.lockDocument](https://mestrelab.com/downloads/mnova/manuals/latest/stubs/MnovaFramework.html#MnovaFramework.Framework.lockDocument) / [unlockDocument](https://mestrelab.com/downloads/mnova/manuals/latest/stubs/MnovaFramework.html#MnovaFramework.Framework.unlockDocument) | An active-document override stack; lock pushes, unlock removes the supplied document or the last entry. | A mutex, object keep-alive, window activation or close protection. Unknown stack state cannot be repaired by speculative unlock calls. |
| Framework.addDocument / MainWindow.getObject | Add to the main-window document list; look up a named object. | A documented UUID-to-window resolver or permission to add an already registered document again. |
| [NMR buffer](https://mestrelab.com/downloads/mnova/manuals/latest/stubs/MnovaNMR.html#MnovaNMR.BaseNMRSpectrum.reData) | Real data are exposed through the buffer protocol. | Copy versus view, writable state, parent lifetime, or invalidation. A successful memoryview conversion cannot supply those missing guarantees. |
| `NMRItem(PageItem)` / `Page.addItem` | Conversion and item-attachment entrypoints exist. | Whether conversion aliases or copies, or attachment transfers native ownership. The installed spectrum example demonstrates intended use, not destruction guarantees. |
| [JSPlugin.evaluate](https://mestrelab.com/downloads/mnova/manuals/latest/stubs/MnovaJS.html#MnovaJS.JSPlugin.evaluate) / evaluateFile | String output; documented execution failure raises RuntimeError. | A supported cross-language native-handle channel, native-object release ordering, or side-effect-free execution. |
| [Python Connection.disconnect](https://mestrelab.com/downloads/mnova/manuals/latest/stubs/MnovaCore.html#MnovaCore.Connection.disconnect) | A connection handle with a disconnect operation returning bool. | A DocumentPlugin close signal, identity payload or completion/cancellation guarantee. Object-wide disconnect and a particular connection handle are different scopes. |
| Installed JS Document / MainWindow reference | Standalone construction, adding a document, window creation and window-close methods are described. | Equivalence to Python session creation, safe inactive-target closure or prompt/completion behavior. `destroy` is not an accepted fallback. |
| Installed JS event handlers | Registration lists `documentClosed` and `activeDocumentChanged`; the removal list does not list those two. | A reliable lifecycle listener contract, callback payload/timing, or supported unregistration for these events. |

Python tutorial, advanced-plugin, UI, debugging and extension references were
also inspected. The bounded review found no additional UUID/window mapping,
close/cancel completion or main-thread scheduling contract. This is a search
result, not proof that no such API exists.

## 3. Execution-route findings

- The [JavaScript overview](https://mestrelab.com/downloads/mnova/manuals/latest/js-overview.html)
  identifies that scripting engine as deprecated and no longer actively
  developed, and recommends Python. This is a maintenance constraint; it does
  not establish removal or inability to run existing scripts.
- The [command-line manual](https://mestrelab.com/downloads/mnova/manuals/latest/js-command-line.html)
  describes forwarding ordinary GUI requests to an existing Mnova instance,
  including when using `-w`. Waiting for a launcher is not process/session
  isolation.
- The [Mnova 17 changelog](https://support.mestrelab.com/kb/article/567-what-s-new-in-mnova-17-changelog/)
  mentions a standalone NMR Python module without naming the initialization and
  exit contract. The generated
  [NMR loader methods](https://mestrelab.com/downloads/mnova/manuals/latest/stubs/MnovaNMR.html#MnovaNMR.__loader__)
  describe a built-in module importer, not a verified standalone SDK entrypoint.
- The [Console product page](https://mestrelab.com/mnova-console) establishes a
  product and downloads. This review did not obtain a complete Python CLI,
  licence, non-forwarding, configuration, file-output or exit-cleanup contract.
  Console is an alternative to investigate, not an accepted executor.
- Public GitHub discovery did not locate a vendor-authenticated binding
  implementation resolving these questions. Matching account names and
  third-party scripts are not authoritative return-policy evidence. No vendor
  source or binary was downloaded or reverse engineered.

The [pybind11 return-policy guide](https://pybind11.readthedocs.io/en/stable/advanced/functions.html#return-value-policies)
explains possible binding policies. It does not disclose which policies Mnova
actually uses for any of these methods.

## 4. Failure analysis updated from retained evidence

The exact frozen experiment source remains identified by SHA-256
`9f6a1c89073507b2ca5cf999baab5488edcc82da14bd543f524091ea3d4ed34d`.
The source hash was checked again; no experiment was rerun.

The [R1 record](SESSION_LIFECYCLE_R1.md) establishes the observed wrong removal:
five session entries became four, the protected synthetic sentinel was absent,
and the intended clean target remained. Independent later sampling matched the
after-state. It does not establish permanent data destruction or the exact
native cause. `Owned document missing or ambiguous` was the harness's failed
postcondition, not a vendor close exception.

The strict unresolved interval starts with the final values sampled by the
pre-operation observer and that observer's scope cleanup. It then includes target
enumeration/release, the close call, target-reference release and post-operation
observation. The old snapshots combine sequential JS and Python reads; they are
not atomic and their recorded values precede some wrapper cleanup. Matching
digests establish matching sampled content, not absence of intermediate changes
or observer side effects.

| Hypothesis / difficulty | Evidence and limitation | What would discriminate it |
| --- | --- | --- |
| Session object and window target differ | Sentinel used a visible main-window route; target used Python session creation. Target/window mapping was not proven. | Version-specific mapping contract and separately verified same-route disposable documents. |
| Wrapper release or retention changes state | Multiple native wrappers cross observation and resolution scopes; binding policies are missing. | Supported retention rules plus observation-only and resolution/release controls. |
| Active-document or lock context affects close | Sentinel was active; final active document changed. Correlation does not prove active-document close semantics. | Documented targeting and lock-stack rules, followed by an isolated exact-target test. |
| Observation is unsafe or misleading | A previous zero-page getter crashed; this snapshot is non-atomic. Repeated reads succeeding do not prove all getters safe. | Scalar-only observer validation before page/item/buffer reads; independent post-scope state. |
| Deferred event or native close implementation | Possible within the unresolved interval; no specific callback/defect has been identified. | Vendor-supported completion evidence or vendor instrumentation. More Python log lines may still not separate native destruction. |

None is assigned a numerical probability. The earlier cross-language crash, the
diagnosed zero-page getter crash and this non-crashing R1 failure remain separate
events. A fix for one is not evidence of a fix for the others.

## 5. Decision and remaining acquisition work

| Item | State |
| --- | --- |
| Installed and public interface descriptions, source boundaries | READY for this review |
| Actual ownership, window target, close/cancel and observer contracts | PARTIAL; vendor clarification needed |
| Standalone NMR / Console execution contract | BLOCKED pending a supported entrypoint and isolation evidence |
| Candidate development route | READY for review in [the route document](NEXT_TECHNICAL_ROUTE.md) |
| Vendor clarification request | [Reviewed message](VENDOR_INTERFACE_QUESTIONS.md) sent after explicit authorization; sender-side readback verified; awaiting technical reply |
| Formal route confirmation / code development | PENDING / NOT STARTED in this phase |

The four question groups in the sent message address the remaining contract
gaps. A future reply must identify applicable versions, preconditions and a
supported example or explicit unsupported status. An example alone does not
complete native acceptance. Keep private correspondence private unless its
publication has been authorized.
