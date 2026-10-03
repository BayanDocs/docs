# DOCS-002: Contributor onboarding and development-environment guides

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | DOCS |
| Repository | docs (+ README links in code repositories) |
| Attach to session | all five repositories |
| Size | S |
| Depends on | CORE-001, DESK-001, WEB-001, SRV-001 (merged), DOCS-001 |
| Unblocks | Human contributors; faster agent onboarding |
| Status | Ready |
| Requirements | — |
| Decisions | ADR-0002, ADR-0027 |
| Specs | — |

## Context

Once each repository has its scaffold and verification gate, contributors (human or agent) need one place that explains how to set up each toolchain on Windows, macOS and Linux and how to run each gate.

## Objective

A tested getting-started guide that takes a newcomer from a clean machine to a passing verification gate in every repository.

## Scope

### In scope

- `developer/getting-started.md`: overview of the repositories and how they fit together, required tools per repository and how to install them on each OS (pinned versions, consistent with ADR-0017), how to run each repository's verification gate.
- One page per repository under `developer/` with deeper setup notes (for example Qt installation for desktop; wasm32 target for core; pnpm setup for web; SQLite and container tooling for server).
- `developer/first-contribution.md`: how work packages, branches, commits (DCO), pull requests and reviews work, for humans.
- Links from each code repository's `README.md` to its developer page.

### Out of scope

User-facing handbook content.

## Deliverables

New pages under `developer/`, README link updates in code repositories.

## Acceptance criteria

- [ ] AC-1 Following the guide in a fresh Linux container, the agent builds and passes the verification gate of core, server and web, and builds desktop (evidence: command log summary).
- [ ] AC-2 Windows and macOS instructions are complete and consistent with CI configuration (cross-checked against the workflow files).
- [ ] AC-3 `scripts/verify.sh` passes.

## Verification

Command log from the fresh container; docs verify script.

## Escalate if

A repository's documented commands do not match its CI; report the discrepancy rather than documenting a workaround.
