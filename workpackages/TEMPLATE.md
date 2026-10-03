# WP-ID: Title

| Field | Value |
|---|---|
| Phase | N — Name |
| Stream | STREAM |
| Repository | where the code goes |
| Attach to session | repositories the agent needs (always include `docs`) |
| Size | S / M / L |
| Depends on | WP IDs (must be Done), or "—" |
| Unblocks | WP IDs |
| Status | Draft / Ready / In progress / In review / Done / Blocked |
| Requirements | requirement IDs |
| Decisions | ADR IDs (binding) |
| Specs | spec files |

## Context

Why this work exists and what the agent needs to know that is not in the linked ADRs and specs.

## Objective

One or two sentences: the outcome.

## Scope

### In scope

- …

### Out of scope

- …

## Deliverables

- Files, crates, tools, reports, documentation.

## Acceptance criteria

- [ ] AC-1 …
- [ ] AC-2 …

Each criterion is testable and the pull request must show evidence for it.

## Verification

Commands the agent runs (and CI runs) to prove the acceptance criteria.

## Notes and pitfalls

Known traps, hints, prior art.

## Escalate if

Situations in which the agent must stop and ask instead of deciding.
