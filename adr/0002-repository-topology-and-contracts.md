# ADR-0002: Repository topology, versioning and cross-repository contracts

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** ARC-01, ARC-03, [plan/03-architecture.md §3](../plan/03-architecture.md#3-repositories-and-their-boundaries), X-101, X-102

## Context

The owner created five repositories: `bayan-core` (Rust), `bayan-desktop` (C++/Qt), `bayan-web` (TypeScript), `bayan-server` (Rust) and `docs`. A monorepo would allow atomic cross-cutting changes, but the split matches the language and toolchain boundaries, keeps each CI simple, and lets agent sessions attach only what they need. The cost of a polyrepo is coordinating changes across repositories.

## Decision

1. **Keep the five repositories.** Responsibilities and prohibitions per repository are as listed in [plan/03-architecture.md §3](../plan/03-architecture.md#3-repositories-and-their-boundaries). The Fidelity Lab lives in `bayan-core` under `lab/` because it shares code with the engine; corpus data is stored outside Git.
2. **Contract-first changes.** A change that crosses a repository boundary starts with a pull request to the relevant spec in `docs` (engine protocol, sync protocol, document model), then the core change, then the shell or server changes.
3. **Versioning.** `bayan-core` follows Semantic Versioning (0.x until 1.0) and tags releases. The engine protocol carries its own integer version, negotiated at startup.
4. **Consumption.**
   - Desktop consumes a **C SDK** per target (static and dynamic libraries, C header, JSON Schema of the protocol), published as release assets with checksums and provenance attestations, pinned by exact version and SHA-256.
   - Web consumes the **WebAssembly package** (`.wasm`, JavaScript glue, TypeScript types), published to npm under `@bayandocs` with provenance, pinned exactly.
   - Server consumes the core **Rust crates** it needs (protocol types, MLS client helpers) as Git dependencies pinned to a tag and commit, until they are published to crates.io.
   - During Phase 0, before the first release, shells may build core from a pinned commit in CI.
5. **Integration.** A nightly workflow builds the shells and server against core `main` and runs their end-to-end suites (X-102), so breakage is found within a day.
6. **No code duplication across repositories.** Logic needed by two shells belongs in core; logic needed by core and server belongs in a core crate that the server depends on.

## Consequences

- Each repository has a single toolchain and a fast, focused CI.
- Cross-repository features take a few sequential pull requests; the contract-first rule keeps them coherent.
- Releases of core become an explicit, auditable event that the shells opt into.

## Alternatives considered

- **Monorepo:** atomic changes and one CI, but mixes Rust, C++, TypeScript toolchains and makes every session clone everything. Rejected given the owner's structure and the agent workflow.
- **Git submodules:** brittle for agents and humans alike.
- **Shells building core from source always:** simpler early, but hides version skew; allowed only in Phase 0.

## Revisit when

More than 30% of merged work packages in a phase need coordinated changes in three or more repositories.
