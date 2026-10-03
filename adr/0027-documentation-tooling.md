# ADR-0027: Documentation tooling

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** DOCS-001, ADR-0017

## Context

The `docs` repository is the knowledge base for agents, contributors, self-hosters and end users. It should render nicely on GitHub as plain Markdown today and as a searchable website later, with as few dependencies as possible (ADR-0017).

## Decision

1. **Plain GitHub-flavored Markdown is the source format,** one paragraph per line, with Mermaid diagrams (rendered natively by GitHub).
2. **mdBook** (a single Rust binary) builds the website, with search, published to GitHub Pages. Mermaid diagrams on the site are rendered by a pinned, self-hosted copy of the Mermaid script or an mdBook preprocessor, chosen in DOCS-001 by dependency cost.
3. **Docs CI:** site build, link checking (lychee) and spell checking (typos), all single-binary tools.
4. **API reference** comes from rustdoc (core, server) and TypeScript declaration output (web), published alongside the site from Phase 1.
5. **Translations** of user-facing documentation later via gettext-based tooling for mdBook (Phase 4 or later).

## Consequences

- Documentation stays readable directly on GitHub, which matters while the site does not exist.
- The toolchain is small and shares the Rust ecosystem's supply-chain controls.

## Alternatives considered

- **Docusaurus, Astro Starlight:** richer themes, but large npm dependency trees.
- **MkDocs with Material:** popular, but Python dependency trees and uncertain long-term maintenance.

## Revisit when

End-user handbook needs (versioning, rich search, translations) exceed mdBook's capabilities.
