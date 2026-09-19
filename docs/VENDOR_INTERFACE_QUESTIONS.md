# Vendor interface clarification request

Date: 2026-09-16. Status: **SENT; AWAITING TECHNICAL REPLY**.

The owner explicitly authorized sending the reviewed message in this task.
Gmail accepted the send at **2026-09-16 11:04:29 UTC** with the SENT label; a
separate thread readback verified the recipient, subject and message body.
This is sender-side evidence, not proof of recipient delivery or a technical
answer. No attachments were sent. The source checkout, private receipts and
licence information were omitted; ordinary mail headers identify the sender.

Recipient: `support@mestrelab.com`. The address is listed in the
[official support terms](https://mestrelab.com/end-user-software-license-agreements),
section 4.2. The alternative official channel is the
[support ticket form](https://support.mestrelab.com/new/). No duplicate form
submission was made. No support entitlement is asserted here. Private message
identifiers remain outside this public document.

## Sent subject

Mnova 17.0.1 Python API: document/window ownership, close completion and isolated execution

## Sent message body

Hello Mestrelab Support,

We are evaluating the supported scripting interfaces for an independent,
host-neutral Mnova automation companion. Could you route this request to the
Python API team and provide version-specific documentation or a minimal supported
example for the contracts below?

Our observed environment is Windows, Mnova 17.0.1 build 41952, with embedded
Python 3.11.15. We have consulted the installed Python reference and examples,
the online manual and Python stubs, and the Mnova 17 changelog. The online manual
identifies itself as v17.0.0.3184c2c, so confirmation for our installed build would
be helpful.

During one bounded experiment using only task-created synthetic/blank inputs, a
protected, active, genuinely modified document was created through the main-window
File New action. A separate clean target was created with
DocumentPlugin.newDocument(), initialized with one empty page, and independently
observed in the session inventory. We had not established that this target had a
corresponding GUI window.

A single sequence resolved the target by UUID, called
DocumentPlugin.closeDocument(target), released the target reference, and sampled
the session again. The recorded inventory changed from five documents to four:
the protected synthetic document was absent, while the intended target remained.
A later independent invocation observed the same resulting state. The three
original document rows and an older synthetic buffer were unchanged. No crash was
observed in this experiment.

We cannot attribute this to the close call alone. The snapshots combine
sequential JavaScript/Python reads and are not atomic. The unresolved interval
also includes the previous observer scope's wrapper cleanup, target enumeration
and release, and later observation. We have stopped native mutations and have
not retried or performed automatic cleanup. We are seeking the supported usage
contract before proposing another isolated diagnostic.

1. **Object and buffer lifetime.** For Document constructors,
   DocumentPlugin.newDocument()/documents(), Document pages/currentPage,
   NMRItem(PageItem), Page.addItem(), and NMRItem.reData/imData, which results are
   owned, borrowed, copied or transferred? Which parents must remain alive, what
   invalidates aliases, and can releasing the last Python wrapper change or
   destroy a session document? Are there additional rules when Python and
   JavaScript refer to the same underlying document? We are not assuming generic
   pybind11 return policies describe these bindings.

2. **Exact document/window closure.** What supported API maps a Document UUID to
   its GUI document window? How do standalone, session-listed and window-backed
   documents differ? For closeDocument(aDoc), must the target be window-backed,
   active, added to Framework, or locked? What is the supported way to close a
   clean inactive target while preserving a different active dirty document?
   Please specify dirty-prompt/cancellation behavior, synchronous versus deferred
   completion, and which existing wrappers become invalid. The documented None
   return does not provide a success/cancellation distinction.

3. **Observation, thread and events.** Which scalar identity/state getters are
   supported for zero-page or closing documents, and on which thread and event
   phase? Is there a documented final-close/cancel observation with a target
   identity? If events are needed, please identify the event owner, payload,
   callback timing and exact unsubscription method. We found Python Connection
   handles, but no DocumentPlugin close signal contract; the JS install/remove
   event-handler lists also differ for document events.

4. **Independent execution.** The Mnova 17 changelog mentions a standalone NMR
   Python module. Please identify its actual public entrypoint, supported sample,
   initialization/shutdown, document/file support and licensing requirements.
   Alternatively, does Mnova Console provide a supported Python execution route
   with documented CLI, exit status and cleanup? We need a process/session that
   cannot forward work into an already open GUI instance, with independently
   scoped configuration and files. The ordinary GUI -w option forwards to an
   existing instance and does not establish this isolation.

Please distinguish documented guarantees, unsupported use, and behavior that
needs a corrected build. A small supported example for each relevant route would
help us define acceptance tests. If these detailed contracts are unavailable,
please identify the supported automation route you recommend for this use case.

Thank you.

## Local technical correction after send

The sent wording `NMRItem.reData/imData` in question 1 names the wrong declaring
class. The documented methods are `BaseNMRSpectrum.reData()` and `imData()`;
the frozen experiment accesses the spectrum through `item.activeSpectrum` before
calling `reData()`. The ownership question concerns that spectrum and its buffer.
The sent body above is preserved verbatim. This clarification has not been sent
as a second message and should be included in any later authorized technical
follow-up if needed.

## How a reply will be evaluated

Record the applicable version/build and classify each answer as a documented
guarantee, example-only guidance, unsupported operation, defect acknowledgement,
or unresolved question. A workaround must specify its preconditions and cannot
serve as acceptance by itself. Ask whether a version-scoped technical summary
may be published before quoting private correspondence publicly.

The [interface review](INTERFACE_CONTRACT_REVIEW.md) and
[candidate technical route](NEXT_TECHNICAL_ROUTE.md) remain planning documents.
No reply alone enables native writes or starts code development.
