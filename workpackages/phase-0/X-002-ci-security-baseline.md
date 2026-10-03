# X-002: CI security baseline — hardened workflows, workflow linting, Scorecard

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | SECURITY |
| Repository | all five |
| Attach to session | all five repositories |
| Size | S |
| Depends on | Each repository has its scaffold workflow (CORE-001, DESK-001, WEB-001, SRV-001, DOCS-001) or can be done alongside them |
| Unblocks | Safe growth of CI in every later WP |
| Status | Ready |
| Requirements | SEC-05, SEC-12 |
| Decisions | ADR-0017, ADR-0025 |
| Specs | [threat-model.md](../../specs/threat-model.md) (T16) |

## Context

GitHub Actions workflows are part of the supply chain (threat T16). The owner's settings will require SHA-pinned actions (owner checklist item 5); this WP makes every repository's workflows meet a hardened standard and keeps them that way with automated checks.

## Objective

Every workflow in every repository is hardened, linted on change, and covered by OpenSSF Scorecard and code scanning.

## Scope

### In scope

- A **workflow conventions** section added to each repository's `AGENTS.md`: top-level `permissions: {}` (or `contents: read`) with per-job grants; `persist-credentials: false` on checkout unless pushing; no `pull_request_target`; no secrets in workflows triggered by pull requests; timeouts and concurrency groups on every job; actions pinned to full SHAs with the version in a trailing comment; tools downloaded in CI pinned by version and verified by checksum.
- A **workflow-lint** job in every repository, triggered on changes to `.github/workflows/**`, running `zizmor` (pinned version, verified download) with zero findings at its default settings, and `pinact run --check --verify-min-age --min-age 1`.
- **OpenSSF Scorecard** workflow (scheduled weekly and on pushes to `main`), results uploaded as code-scanning results.
- **CodeQL** code scanning for the languages present (C++ in desktop, JavaScript/TypeScript in web, GitHub Actions workflows everywhere, Rust where CodeQL supports it at the time; record which).
- Fix any findings in existing workflows.

### Out of scope

- Repository settings (owner).
- The supply-chain dependency checks (X-003).

## Deliverables

One pull request per repository.

## Acceptance criteria

- [ ] AC-1 `zizmor` reports zero findings on all workflows in all repositories (output in the pull request).
- [ ] AC-2 `pinact` check passes in all repositories.
- [ ] AC-3 Scorecard and CodeQL workflows run successfully on `main` (links in the pull request); Scorecard score recorded as a baseline.
- [ ] AC-4 Each repository's `AGENTS.md` contains the workflow conventions.
- [ ] AC-5 All tools used in workflows are pinned and checksum-verified, and every pinned version is at least 24 hours old.

## Verification

Workflow runs on a test branch showing the lint job failing on a deliberately unpinned action and passing after the fix.

## Notes and pitfalls

- CodeQL for compiled languages needs a build; reuse the scaffold's build steps.
- Scorecard flags missing branch protection and similar settings that only the owner can change; list them in "Open questions for the owner" rather than working around them.

## Escalate if

A tool's latest version is younger than 24 hours and no older version supports the needed check.
