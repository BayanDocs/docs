# X-001: Repository baseline — governance files, PR template, DCO, licenses, REUSE

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | RELEASE / SECURITY |
| Repository | all five: bayan-core, bayan-desktop, bayan-web, bayan-server, docs |
| Attach to session | all five repositories |
| Size | M |
| Depends on | Part A: — · Part B: owner's decision on ADR-0003 §4 (app-store permission), and its final reviewed text if adopted |
| Unblocks | X-002, all later contribution flows |
| Status | Ready |
| Requirements | SEC-09 |
| Decisions | ADR-0003, ADR-0017, ADR-0001 |
| Specs | — |

## Context

Every repository needs the same contribution scaffolding before many agents start working in parallel: how to contribute, how to report vulnerabilities, the pull request hand-off template, sign-off of commits (Developer Certificate of Origin), and, once the owner confirms ADR-0003, license files and per-file license headers checked by the REUSE tool. The repositories currently contain only `README.md`, `AGENTS.md` and `CLAUDE.md`. The licenses were confirmed by the owner on 2026-10-04 (ADR-0003, explained in `docs/LICENSING.md`); only the app-store permission (ADR-0003 §4) is still open.

## Objective

Identical, correct governance and contribution files in all five repositories, plus a DCO check, so that every later pull request follows the same rules.

## Scope

### In scope

**Part A (start immediately):**

- `CONTRIBUTING.md`: how to propose changes, Conventional Commits, DCO sign-off (`git commit -s`), link to `docs/AGENTS.md` and `docs/plan/06-agent-workflow.md`, the dependency policy summary (ADR-0017).
- `SECURITY.md`: report vulnerabilities through GitHub private vulnerability reporting; supported versions (pre-1.0: latest only); response targets from `docs/plan/07-quality-security-testing.md`; a placeholder for the security contact email (ask the owner).
- `CODE_OF_CONDUCT.md`: the Contributor Covenant 2.1, copied verbatim from its official source, with a contact placeholder.
- `.github/pull_request_template.md`: the hand-off template from `docs/plan/06-agent-workflow.md`, verbatim.
- `.github/ISSUE_TEMPLATE/`: bug report, feature request, and work-package templates (forms or Markdown), plus `config.yml`.
- `CODEOWNERS`: the owner as default owner (ask for the GitHub handle if unknown).
- `.editorconfig` and `.gitattributes` (LF line endings, binary file types, `*.docx`/`*.pdf`/`*.ttf`/`*.otf`/`*.png` as binary).
- A **DCO check workflow** in each repository implemented as a small script in the workflow (no third-party action), following the AI-assisted contribution rule in ADR-0003: commits by human authors must carry a `Signed-off-by` line matching their author; commits authored by recognized agent identities (listed in a small config file) must carry agent attribution trailers instead, and the pull request description must then contain a `Signed-off-by` line from the human submitter. Document the rule in `CONTRIBUTING.md` and follow the workflow rules in ADR-0017 (SHA-pinned actions, minimal permissions).

**Part B (only after the owner has decided ADR-0003 §4):**

- `LICENSE` file per repository with the exact license text from its official source: GPL-3.0 text for bayan-core, bayan-desktop and bayan-web (license expression `GPL-3.0-or-later`); AGPL-3.0 text for bayan-server (`AGPL-3.0-or-later`); CC BY 4.0 for docs. Also a REUSE `LICENSES/` folder in each repository holding the full text of every license used there (including `Apache-2.0`, `MIT-0` and `CC0-1.0` where applicable), taken from the SPDX license-list data and verified by checksum.
- **Apache-2.0 areas** declared in REUSE: `docs/specs/protocols/**`, `bayan-core/crates/bayan-protocol/**` and `bayan-server/integrations/**` (create the directories with a short README if they do not exist yet). **CC0-1.0** for template and sample-content directories once they exist. CC-BY-4.0 (with MIT-0 for code snippets) for the rest of docs.
- **App-store permission:** only if the owner adopted ADR-0003 §4, add its final, lawyer-reviewed text as a separate file (for example `LICENSES/LicenseRef-BayanDocs-App-Store-Permission.txt`, or the form REUSE and SPDX recommend for custom license additions at the time) and reference it from the license expressions and READMEs of bayan-core, bayan-desktop and bayan-web. Never use the draft wording from the ADR.
- `CONTRIBUTING.md` explains inbound = outbound per file or directory and links to `docs/LICENSING.md`.
- A REUSE lint job in CI with the `reuse` tool pinned by exact version and hash.
- Set the `license` field in manifests that exist by then (for example `Cargo.toml` `[workspace.package]`, with a separate value for `bayan-protocol`).

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
- [ ] AC-4 (Part B) Each `LICENSE` and `LICENSES/` file is byte-identical to the official text (checksum comparison shown); `reuse lint` passes in CI in every repository; REUSE output shows Apache-2.0 for exactly the three Apache-2.0 areas.
- [ ] AC-5 Every workflow added pins actions to full commit SHAs, sets minimal `permissions:`, and does not use `pull_request_target`.
- [ ] AC-6 No update-bot configuration is added anywhere.

## Verification

- Render check of each Markdown file on GitHub.
- CI runs of the DCO workflow (failing and passing cases).
- `reuse lint` locally and in CI (Part B).

## Notes and pitfalls

- Copy license and Code of Conduct texts from their official sources; never retype or paraphrase them.
- The DCO check must handle merge commits and co-authored commits sensibly; document the rule in `CONTRIBUTING.md`.

## Escalate if

- The owner has not yet decided ADR-0003 §4: deliver Part A only and say so.
- The owner's GitHub handle or security contact email is unknown: use clearly marked placeholders and list them under "Open questions for the owner".
