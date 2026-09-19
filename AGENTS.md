# Mnova Companion contributor entrypoint

Read DEVELOPMENT_PRINCIPLES.md (Chembridge 2026-09-19.1), README.md and docs/STATUS.md before work. Also read RUNTIME_LIFECYCLE.md, governance/OWNERSHIP.md and the product record docs/LIFECYCLE.md for lifecycle or ownership work. This repository owns Mnova Companion implementation. The approved design is maintained in the Chembridge hub at plans/MNOVA_COMPANION_PLAN.md.

Use one host-neutral execution core and thin host adapters. Keep Mnova native calls inside a trusted packaged adapter. Do not expose arbitrary Python, JavaScript, shell execution or global application shutdown as public tools. Preserve raw input files and every unrelated/unsaved user document. Native trigger, owned-document handling, save/reopen, licence/module, output-contract, host delivery and model acceptance require separate evidence.

Never copy vendor binaries, vendor API source, licence contents, credentials, private coursework, user data or machine/account identifiers into public source or verification. Use synthetic/public fixtures; local execution artifacts belong in ignored .local/ or a user-selected private destination. Public documentation is English.

Python 3.12 is the external runtime target; Mnova's embedded Python is separate. Setup and checks are recorded in README.md as implemented. Run focused tests, then the complete documented checks after integration. No product capability is accepted solely from a mock or process exit.

Parallel writers must own disjoint files. The root coordinator owns shared contracts, package manifests, dependency locks, release state and integration. Native execution is single-owner and serial. Do not start Mnova from a second worker.

Routine collaboration within existing Chembridge tasks is preauthorised under shared section 11. Preserve repository ownership and acceptance scope. Runtime users need no source checkout or coding project; record packaging gaps honestly.

One Astra Max Product owner holds long-term implementation responsibility; Governance High reviews shared contracts and incidents. The verified takeover is complete. Preserve the explicit pre-existing dirty-file checkpoint and historical acceptance records. Native mutations and target close remain disabled; I0, P1, installed P0 migration and scientific acceptance retain separate gates. Baseline adoption is not runtime conformance.
