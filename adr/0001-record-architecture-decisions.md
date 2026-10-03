# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner (initial planning session), at the owner's request to own the plan
- **Related:** [AGENTS.md](../AGENTS.md), [plan/06-agent-workflow.md](../plan/06-agent-workflow.md)

## Context

BayanDocs will be built over years, mostly by AI agents working in separate sessions without shared memory. Without a durable record of why things are the way they are, each session would re-litigate settled questions or silently drift from them. The owner is not yet an expert in the languages and domains involved and needs decisions explained in a form they can review.

## Decision

1. Every significant technical or policy decision is recorded as an ADR in this folder, numbered sequentially, using [0000-template.md](0000-template.md).
2. **Accepted ADRs are binding** on all repositories. Work that conflicts with one stops and escalates.
3. ADRs are not rewritten after acceptance. A changed decision gets a new ADR that supersedes the old one (or, for small clarifications, a dated "Amendment" section at the end). The index in [README.md](README.md) is updated in the same pull request.
4. An ADR may be **Accepted with a validation gate**: the decision stands, but a named spike or work package must confirm explicit criteria. If they fail, the next gate review amends the ADR.
5. Agents may draft ADRs (status Proposed) at any time. The following require the **owner's explicit confirmation** before acceptance: licensing and trademarks; anything that spends money; changes to the product principles or the Fidelity Contract; changes to the supply-chain policy; adding a repository or a programming language; anything that weakens a privacy or security promise.
6. All other ADRs can be accepted by a planning session (gate review or a dedicated decision session), with a plain-language summary to the owner.
7. Every ADR names its "revisit when" triggers so that reconsideration is driven by evidence, not by a new session's taste.

## Consequences

- New agents can get up to speed by reading the index and the ADRs relevant to their work package.
- Disagreement is channelled into proposals with evidence rather than code that quietly diverges.
- There is a small overhead per decision, which is intended.

## Alternatives considered

- **Decisions only in pull request descriptions:** not discoverable, not binding.
- **A single living architecture document:** loses the history of why, and invites silent edits.
