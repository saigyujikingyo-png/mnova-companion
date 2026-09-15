# Current-device Codex preview installation

This is a developer-assisted, current-device installation of source version
`0.1.0.dev1`. It is not a general installer or a native NMR workflow release.

## Installed behavior

The personal Codex plugin is `mnova-companion@personal`. Its icon is the original
asset in [assets](../assets/DESIGN.md). The installed MCP configuration starts a
private, non-editable Python environment with `python -I -m mnova_companion`.
The runtime lives under the current user's local application-data directory;
it does not import the development checkout. The personal plugin source is under
the user's `plugins/mnova-companion` directory, with a separate host-managed cache.
The source manifest gains its concrete `.mcp.json` reference in that private copy.
Machine-specific absolute runtime paths are never committed to this repository.

The installation uses the existing Python 3.12.14 base and locked production
dependencies. It is independent of the Git checkout, but its virtual environment
still depends on that Python base. Copying it to a new device is not supported.
The runtime contains 45,991,717 bytes across 2,010 files at the time of inspection;
this excludes the shared Python base, host cache and generated icon.

Input roots default to an empty list. This preview can report state, describe
contracts and inspect registered artifacts. Native requests return an explicit
unavailable-capability result. There is no graphical input-root selector yet.

## Verification and use

Installation was performed with the official personal-marketplace scaffold and
`codex plugin add`, followed by installed/enabled inventory readback. Its cached
icon hash matches the repository asset. From a temporary working directory, the
installed runtime completed real MCP discovery and calls for all six tools,
with schema validation, text/structured parity and expected error branches.
Existing personal-plugin records and earlier marketplace entries were preserved.
See the [installation receipt](../acceptance/installation_20260915.json).

Start a new Codex task to load the newly installed tools, then request a Mnova
Companion status check. A model-driven call in that new task is a separate gate;
it has not been claimed from the direct protocol test. No native process was
started by the installation verification.

## Update, recovery and removal

For icon, metadata or connection updates, use the official plugin-creator
cachebuster helper on the actual local source, validate it, then run
`codex plugin add mnova-companion@personal` again. This does not update the wheel
in the separate non-editable runtime. A code upgrade must separately build and
verify a new wheel, install it in a new private versioned runtime, update the
private MCP configuration, and repeat installed-runtime protocol checks while
retaining the old runtime for rollback. No automated runtime-upgrade flow has
been implemented or accepted here. Do not edit host cache or registration
internals. The initial install encountered a source
directory mismatch: the CLI resolved `./plugins/mnova-companion` from the user
home. Placing the prepared copy at that observed path resolved the install error;
no marketplace source rewrite or reordering was needed.

Removal through Codex's plugin UI or `codex plugin remove mnova-companion@personal`
removes the host integration. The separate private runtime and user state require
their own intentional cleanup. Removal, reinstallation after removal, upgrades,
and clean-device operation have not been tested. No public release bundle or
double-click installer is provided by this checkpoint.
