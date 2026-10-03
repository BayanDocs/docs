# ADR-0025: Quality gates — determinism, fidelity, fuzzing, performance

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** FID-02…FID-04, SEC-07, PERF-08, [plan/07](../plan/07-quality-security-testing.md), [specs/fidelity-lab.md](../specs/fidelity-lab.md), LAB-106, LAB-107

## Context

Most code will be written by agents and reviewed by a non-expert owner. Quality must therefore be enforced by automated gates that make regressions impossible to merge unnoticed.

## Decision

1. **Determinism gate (core):** a defined determinism corpus is laid out and rasterized (reference mode) on Linux x86-64, Windows x86-64, macOS arm64 and wasm32 (Node and a headless browser); layout and pixel hashes must be identical. A subset runs on every pull request; the full corpus nightly.
2. **Fidelity gate (core, from Phase 1):** on every pull request, the fast public subset is compared with stored Word ground truth. A drop in page-break or line-break agreement beyond the tolerance (initially any document losing agreement it previously had) blocks merging unless the pull request is labeled `fidelity-change`, explains the change, and increments the layout epoch if output changes intentionally. Nightly runs cover the full public corpus; weekly runs cover the private corpus.
3. **Round-trip gate:** open-save-open must be content-identical and untouched parts byte-identical for the public corpus.
4. **Fuzzing gate:** each parser has a fuzz target; short fuzz runs on every pull request touching it, continuous fuzzing on a schedule; any crash is a release blocker.
5. **Performance gate:** benchmarks for the budgets in [plan/02](../plan/02-requirements.md#perf--performance-and-resources) run nightly and on demand; a regression above 5% fails unless accepted with justification.
6. **Static gates:** formatting, linting with warnings as errors, type checking, supply-chain checks (ADR-0017), workflow security linting, and license compliance in every repository.
7. **Snapshot discipline:** snapshot and golden-file updates must be reviewed and explained in the pull request; blanket "accept all" updates are rejected by reviewers.
8. **No coverage percentage targets.** Instead, every behavior change carries tests, and reviewers check that tests would fail without the change.
9. **Gates are never weakened to pass a change** ([AGENTS.md §4](../AGENTS.md#4-the-verification-gate-is-sacred)).

## Consequences

- CI is extensive; macOS and Windows runners are free for public repositories.
- Some changes need lab evidence before merging, which slows layout work deliberately.

## Alternatives considered

- **Manual QA before releases:** cannot scale with agent throughput or a single reviewer.

## Revisit when

CI time exceeds about 30 minutes for pull-request gates; then shard or move more to nightly runs without dropping coverage.
