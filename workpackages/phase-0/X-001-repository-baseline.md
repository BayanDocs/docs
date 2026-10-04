# X-001: Repository baseline — governance files, PR template, DCO, REUSE check

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | RELEASE / SECURITY |
| Repository | all five: bayan-core, bayan-desktop, bayan-web, bayan-server, docs |
| Attach to session | all five repositories |
| Size | M |
| Depends on | — |
| Unblocks | X-002, all later contribution flows |
| Status | Ready |
| Requirements | SEC-09 |
| Decisions | ADR-0003, ADR-0017, ADR-0001 |
| Specs | — |

## Context

Every repository needs the same contribution scaffolding before many agents start working in parallel: how to contribute, how to report vulnerabilities, the pull request hand-off template, sign-off of commits (Developer Certificate of Origin), and a CI check that keeps the REUSE licensing information complete. The licenses are already in force (ADR-0003, owner decision of 2026-10-04): every repository contains `LICENSE`, a `LICENSES/` folder and `REUSE.toml`, added in the planning session and passing `reuse lint` 6.2.0 (checksums under Notes). The repositories otherwise contain only `README.md`, `AGENTS.md` and `CLAUDE.md` (plus `integrations/README.md` in bayan-server and `scripts/` in docs).

## Objective

Identical, correct governance and contribution files in all five repositories, plus a DCO check, so that every later pull request follows the same rules.

## Scope

### In scope

**Part A: contribution scaffolding**

- `CONTRIBUTING.md`: how to propose changes, Conventional Commits, DCO sign-off (`git commit -s`), link to `docs/AGENTS.md` and `docs/plan/06-agent-workflow.md`, the dependency policy summary (ADR-0017).
- `SECURITY.md`: report vulnerabilities through GitHub private vulnerability reporting; supported versions (pre-1.0: latest only); response targets from `docs/plan/07-quality-security-testing.md`; a placeholder for the security contact email (ask the owner).
- `CODE_OF_CONDUCT.md`: the Contributor Covenant 2.1, copied verbatim from its official source, with a contact placeholder.
- `.github/pull_request_template.md`: the hand-off template from `docs/plan/06-agent-workflow.md`, verbatim.
- `.github/ISSUE_TEMPLATE/`: bug report, feature request, and work-package templates (forms or Markdown), plus `config.yml`.
- `CODEOWNERS`: the owner as default owner (ask for the GitHub handle if unknown).
- `.editorconfig` and `.gitattributes` (LF line endings, binary file types, `*.docx`/`*.pdf`/`*.ttf`/`*.otf`/`*.png` as binary).
- A **DCO check workflow** in each repository implemented as a small script in the workflow (no third-party action), following the AI-assisted contribution rule in ADR-0003: commits by human authors must carry a `Signed-off-by` line matching their author; commits authored by recognized agent identities (listed in a small config file) must carry agent attribution trailers instead, and the pull request description must then contain a `Signed-off-by` line from the human submitter. Document the rule in `CONTRIBUTING.md` and follow the workflow rules in ADR-0017 (SHA-pinned actions, minimal permissions).

**Part B: licensing follow-through** (the license files themselves already exist; do not replace them)

- `CONTRIBUTING.md` explains inbound = outbound per file or directory (for bayan-core, bayan-desktop and bayan-web including the BayanDocs App Store Permission), the Apache-2.0 areas and their rules, and links to `docs/LICENSING.md`.
- A **REUSE lint job** in CI in every repository, with the `reuse` tool pinned by exact version and hashes (reuse 6.2.0 has no wheel for current Python versions on Linux: build it from its hash-pinned source archive with a hash-pinned `poetry-core`, as `docs/scripts/cloud-environment-setup.sh` does).
- Confirm that each `LICENSE` and `LICENSES/` file still matches its official source (checksum table under Notes) and keep `reuse lint` passing as files are added.
- When a directory for templates, sample content or default styles is created, declare it `CC0-1.0` in `REUSE.toml` and add the text with `reuse download CC0-1.0` (likewise `OFL-1.1` for fonts made by the project).
- Set the `license` field in manifests that exist by then. In `Cargo.toml` use `GPL-3.0-or-later WITH AdditionRef-BayanDocs-App-Store-Permission` (cargo-deny rejects `LicenseRef-` after `WITH`), `Apache-2.0` for `bayan-protocol`, and `AGPL-3.0-or-later` in bayan-server; REUSE metadata keeps the `LicenseRef-` form (ADR-0003 §4, "Identifier").

### Out of scope

- Build and test workflows (each repository's scaffold WP).
- Repository settings such as branch protection (owner, checklist items 3–6).
- Any Dependabot or Renovate configuration (forbidden by ADR-0017).

## Deliverables

One pull request per repository (or one per repository for Part A and one for Part B), each with the hand-off template filled in.

## Acceptance criteria

- [ ] AC-1 All Part A files exist in all five repositories and render correctly on GitHub.
- [ ] AC-2 The pull request template contains every section of the hand-off template, in order.
- [ ] AC-3 The DCO workflow fails on an unsigned human-authored commit and on an agent-authored pull request without the human submitter's sign-off in its description, and passes in the compliant cases; evidence (test branch runs or a scripted test of the check logic) is in the pull request.
- [ ] AC-4 (Part B) `reuse lint` passes in CI in every repository; the checksums of the `LICENSE` and `LICENSES/` files match the table under Notes (comparison shown); REUSE output shows Apache-2.0 for exactly the Apache-2.0 areas that contain files.
- [ ] AC-5 Every workflow added pins actions to full commit SHAs, sets minimal `permissions:`, and does not use `pull_request_target`.
- [ ] AC-6 No update-bot configuration is added anywhere.

## Verification

- Render check of each Markdown file on GitHub.
- CI runs of the DCO workflow (failing and passing cases).
- `reuse lint` locally and in CI.

## Notes and pitfalls

- Copy license and Code of Conduct texts from their official sources; never retype or paraphrase them.
- The DCO check must handle merge commits and co-authored commits sensibly; document the rule in `CONTRIBUTING.md`.
- **License files added on 2026-10-04** (SHA-256). `LICENSE` files come from gnu.org, apache.org and creativecommons.org; `LICENSES/` files from the SPDX License List data, version 3.29.0, identical to `reuse download`:

| File | Source | SHA-256 |
|---|---|---|
| `LICENSE` in bayan-core, bayan-desktop, bayan-web | https://www.gnu.org/licenses/gpl-3.0.txt | `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` |
| `LICENSE` in bayan-server | https://www.gnu.org/licenses/agpl-3.0.txt | `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0` |
| `LICENSE` in docs | https://creativecommons.org/licenses/by/4.0/legalcode.txt | `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411` |
| `integrations/LICENSE` (server), `specs/protocols/LICENSE` (docs) | https://www.apache.org/licenses/LICENSE-2.0.txt | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| `LICENSES/GPL-3.0-or-later.txt` | SPDX v3.29.0 | `fb981668c18a279e285fc4d83fba1e836cc84dd4daa73c9697d3cfd2d8aca6e0` |
| `LICENSES/AGPL-3.0-or-later.txt` | SPDX v3.29.0 | `d8a6cc31abc16b6748c7a21f21611f5a1ec33f67d22ca23d7da1c19b95496bee` |
| `LICENSES/Apache-2.0.txt` | SPDX v3.29.0 | `074e6e32c86a4c0ef8b3ed25b721ca23aca83df277cd88106ef7177c354615ff` |
| `LICENSES/CC-BY-4.0.txt` | SPDX v3.29.0 | `d557539df68e771cc1eedcc91d13f70fca930e508d11eedcafa4b15db49e3744` |
| `LICENSES/MIT-0.txt` | SPDX v3.29.0 | `59746d6285ffa44bfc7ecada352aa5d6a20dc8eab418a60ce091cc739012c135` |
| `LICENSES/LicenseRef-BayanDocs-App-Store-Permission.txt` | ADR-0003 §4, version 1.0 | `d06381577628681f6970d6da7edfc189df7b29140186bd245a7807718ff8d38a` |

## Escalate if

- The owner's GitHub handle or security contact email is unknown: use clearly marked placeholders and list them under "Open questions for the owner".
