# Agent Operating Manual (canonical)

This file is the canonical set of rules for every AI agent (and human) working on BayanDocs, in any repository. Each code repository has its own `AGENTS.md` with a condensed copy of these rules plus repository-specific instructions; if they ever disagree, this file wins and the discrepancy should be reported.

## 1. Orientation: read before you act

1. Read this file.
2. Read the work package (WP) brief you were given, in [workpackages/](workpackages/README.md).
3. Read every ADR and spec the brief links to. Accepted ADRs in [adr/](adr/README.md) are binding.
4. Read the target repository's own `AGENTS.md` and existing code before changing it.

If you were not given a work package, you are in a planning, review or maintenance session; follow the matching session prompt in [plan/06-agent-workflow.md](plan/06-agent-workflow.md).

In BayanDocs cloud sessions the project's tools are preinstalled at pinned versions by [scripts/cloud-environment-setup.sh](scripts/cloud-environment-setup.sh); run `bayandocs-tools` to list them. If a tool is missing, install the version pinned in that script (never a newer one) and mention it in your pull request.

## 2. Authority and scope

- **ADRs are binding.** If a WP conflicts with an Accepted ADR, the ADR wins: stop and report the conflict. To change a decision, write a new ADR with status `Proposed` (or an amendment to the existing one) in a separate pull request to this repository. Do not implement against a proposal until the owner accepts it.
- **Stay inside the WP's scope.** Do what the brief asks, completely, and nothing else. Record anything else you discover as a follow-up in your pull request's handoff notes (and, if substantial, as a draft WP).
- **Do not refactor unrelated code**, rename public APIs, or reformat files you are not otherwise changing.
- **Clean-room rule.** Learn Microsoft Word's behavior only from public specifications (ECMA-376, ISO/IEC 29500, the [MS-*] open specifications) and black-box observation of its output. Never decompile, disassemble or debug Microsoft software, and never copy code from projects whose license is incompatible with the target repository or directory (for example, GPL-incompatible code into a GPL repository, or any GPL or AGPL code into an Apache-2.0 area).
- **Licensing areas (ADR-0003, [LICENSING.md](LICENSING.md)).** bayan-core, bayan-desktop and bayan-web are GPL-3.0-or-later with the BayanDocs App Store Permission; bayan-server is AGPL-3.0-or-later; this repository is CC BY 4.0 (its scripts, configuration files and CI workflows MIT-0); in every repository the shared contribution tooling (`.github/`, `.editorconfig` and `.gitattributes`) is MIT-0 (ADR-0003, amendment of 2026-10-06). The Apache-2.0 areas (`docs/specs/protocols/`, `bayan-core/crates/bayan-protocol/`, `bayan-server/integrations/`) must never contain, copy from or depend on GPL or AGPL code, so that anyone can integrate with BayanDocs under any license. Each repository's `REUSE.toml` records which license applies to which files and its `LICENSES/` folder holds the full texts; keep `reuse lint` passing, and add a new license text only with `reuse download <SPDX-ID>`.

## 3. Branches, commits and pull requests

- Work on the branch you were given. Never push to `main` directly, never force-push a branch someone else is using, and never rewrite published history.
- Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat(layout): …`, `fix(opc): …`, `docs: …`, `chore(deps): …`).
- Follow the Developer Certificate of Origin rules in each repository's `CONTRIBUTING.md` once work package X-001 has enabled the DCO check. Agents do **not** sign off commits themselves (a DCO sign-off is a legal certification only a person can make); they add their attribution trailers, and the human submitter certifies the work (ADR-0003).
- Keep commits small and logical. A pull request implements one WP (or one clearly bounded part of one).
- Your pull request description must follow the **handoff template** in [plan/06-agent-workflow.md](plan/06-agent-workflow.md#hand-off-template): summary, WP link, acceptance-criteria checklist with evidence, verification output, deviations, follow-ups, open questions, and notes for the next agent.

## 4. The verification gate is sacred

- Run the repository's full verification gate before every push (each repo's `AGENTS.md` names the command). CI also runs the DCO check and `reuse lint` on every pull request in every repository ([CONTRIBUTING.md](CONTRIBUTING.md#developer-certificate-of-origin)); they must pass too. Both run the pull request's own copy of their files, so a pull request can change the checks that judge it: treat every change under `.github/` as security-relevant in review.
- Never weaken, skip, disable, quarantine or delete a test, lint, check or CI job to make a change pass. If a check is genuinely wrong, fix the check in its own commit and explain why, or escalate.
- Every behavior change has tests. Every bug fix has a regression test. Any change that alters layout output must include Fidelity Lab evidence (see [specs/fidelity-lab.md](specs/fidelity-lab.md)).

## 5. Dependencies (strict — see ADR-0017)

- **Never add automated version-update bots**: no `.github/dependabot.yml`, no Renovate, no equivalent. GitHub Dependabot *security alerts* stay enabled as a repository setting; they open no pull requests.
- **Minimum age 24 hours.** Never install, pin or upgrade to a dependency version published less than 24 hours ago. Check the publish time (crates.io API `created_at`, npm `time`, release date) and state it in the PR.
- **Exact pins and committed lockfiles.** No version ranges in manifests where the ecosystem allows exact pins; `Cargo.lock` and `pnpm-lock.yaml` are always committed; CI builds with `--locked` / `--frozen-lockfile`.
- **Install scripts are disabled** (`ignore-scripts=true` and pnpm's build-script allowlist). Do not enable a package's install script without an approved justification in the PR.
- **Audit and lockfile-lint gates must stay green.** Licenses must be on the allowlist in ADR-0017.
- **Every new dependency is justified in the PR**: what it does, why we cannot reasonably write it, alternatives considered, license, maintenance status, publish date of the pinned version, and how many transitive dependencies it adds. Prefer fewer, well-maintained dependencies.
- Routine upgrades happen only in the batched dependency-update session ([plan/06-agent-workflow.md](plan/06-agent-workflow.md#monthly-dependency-update-session)), never as drive-by changes. If a security alert requires an immediate update, follow the same session procedure for just that alert.
- If a repository documents its dependency posture (ADR or handoff doc), update that document in the same pull request as any posture change.

## 6. Security and privacy

- Treat every document, image, font, clipboard payload and network message as hostile input. Parsers must enforce size, depth and count limits and must have fuzz targets.
- No `unsafe` Rust outside crates designated for FFI, without an approved ADR or WP that authorizes it, and every `unsafe` block carries a `// SAFETY:` comment.
- No C or C++ libraries for parsing untrusted input when a maintained memory-safe alternative exists (ADR-0006).
- Never log, print, or include document content, file names, or user identifiers in logs, crash reports, telemetry, test snapshots that leave the machine, or error messages sent to servers.
- No telemetry, analytics, or third-party network calls at runtime. The core never opens sockets; hosts provide transport (ADR-0012).
- Never fetch resources referenced by a document (linked images, templates, INCLUDE fields, remote fonts) without explicit user consent; never execute DDE, OLE or macros automatically (ADR-0023).
- Never commit secrets, tokens, private keys, or real personal documents. Test documents must have a recorded license or be synthetic.
- Never roll your own cryptography. Use the libraries chosen in ADR-0016, and escalate any cryptographic design question.

## 7. Determinism (core repository)

Layout and rendering must produce identical results on every platform (ADR-0004, ADR-0005):

- Layout arithmetic uses the integer Bayan Layout Unit (BLU) types from `bayan-units`, never floating point.
- No platform floating-point transcendental functions (`sin`, `cos`, `exp`, `powf`, …) in layout or rendering paths; use the deterministic implementations provided by `bayan-units`.
- No iteration-order dependence on hash maps in anything that affects output; use ordered maps or deterministic hashers.
- No dependence on system time, locale, installed fonts, environment variables or thread scheduling unless passed in explicitly through the engine's host interfaces.

## 8. When to stop and ask

Stop, write down the problem, list the options with your recommendation, and hand back to the owner instead of guessing when:

- the brief is ambiguous or its acceptance criteria cannot be met as written;
- the work conflicts with an Accepted ADR or would need a new architectural decision;
- a dependency you need violates the dependency policy or its license is unclear;
- the task touches cryptography, authentication, authorization, or key management in a way the brief does not spell out;
- you need something only the owner can provide (accounts, hardware such as the Word reference machine, paid services, legal judgement).

## 9. Writing for the owner

The owner is learning Rust, C++ and TypeScript as the project progresses. In pull requests and reports, explain what you did and why in plain language, define jargon the first time you use it, and point to the file and line that matters. When you give the owner text to copy (prompts, commands with prose, messages), write it as flowing paragraphs without hard-wrapped line breaks.

## 10. Rules specific to this `docs` repository

- Markdown, one paragraph per line (no hard wrapping), ATX headings, relative links between documents.
- ADRs are append-only in spirit: to change an Accepted ADR, add a new ADR that supersedes it (or a dated amendment section), and update the index in [adr/README.md](adr/README.md).
- Work package briefs follow [workpackages/TEMPLATE.md](workpackages/TEMPLATE.md). Keep the index in [workpackages/README.md](workpackages/README.md) in sync when adding or re-scoping WPs.
- Every Markdown page is listed in `SUMMARY.md`, the navigation of the website that mdBook builds from this repository (ADR-0027). Links must work both on GitHub and on the website: use relative links to `.md` files (never absolute site paths), and link to a page rather than to a folder.
- Verification gate: run `scripts/verify.sh`. It builds the website and checks the navigation, ADR and work package IDs, the vendored Mermaid script, links (between files strictly, including `#anchors`; external links with a one-day cache) and spelling (project dictionary in `typos.toml`), and runs the unit tests of the scripts (`scripts/tests/`). Its tools are installed at pinned versions by `scripts/dev-setup.sh`; BayanDocs cloud sessions already have them. The `reuse lint` workflow pins REUSE in `.github/reuse/` (`requirements.txt`: REUSE 6.2.0 and its dependencies; `build-requirements.txt`: the build backend poetry-core 2.5.0), at exact versions with SHA-256 hashes, installed with `pip --require-hashes` as prebuilt wheels except REUSE itself, which is built from its hash-pinned source archive without build isolation. The pins equal `req_reuse` and `req_poetry_core` in `scripts/cloud-environment-setup.sh` (`scripts/tests/test_repository_baseline.py` checks this), are identical in all five repositories, and change only in the monthly dependency session, in all five together. Use `scripts/verify.sh --offline` only where external sites cannot be reached, and say so in your pull request; CI always checks external links.
