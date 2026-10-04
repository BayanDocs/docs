# DOCS-001: Knowledge-base site (mdBook) and docs CI

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | DOCS |
| Repository | docs |
| Attach to session | docs |
| Size | S |
| Depends on | — |
| Unblocks | DOCS-002, published documentation |
| Status | Ready |
| Requirements | — |
| Decisions | ADR-0027, ADR-0017 |
| Specs | — |

## Context

The knowledge base is plain Markdown that renders on GitHub today. ADR-0027 chose mdBook to publish it as a searchable site, with link and spell checking in CI using single-binary tools.

## Objective

A published mdBook site of the whole knowledge base with a CI gate that keeps links and spelling correct, without breaking how the Markdown renders on GitHub.

## Scope

### In scope

- `book.toml` and `SUMMARY.md` covering `README.md`, `LICENSING.md`, `AGENTS.md`, `plan/`, `adr/`, `specs/`, `workpackages/`.
- Placeholder folders with a `README.md` each: `handbook/` (user handbook), `developer/` (contributor and developer guides), `deploy/` (self-hosting), `api/` (API references).
- Mermaid rendering on the site: choose between a pinned, vendored `mermaid` script with its checksum recorded, or an mdBook preprocessor, by lowest dependency cost; document the choice.
- `scripts/verify.sh`: mdBook build, `lychee` link check (internal links strictly; external links with caching and a small allowlist for flaky sites), `typos` spell check with a project dictionary (technical terms such as Loro, harfrust, skrifa, OOXML).
- CI workflow running `scripts/verify.sh` on pull requests; deployment workflow to GitHub Pages on `main` (with minimal permissions). Tools installed from release binaries pinned by version and verified by checksum.
- Update `AGENTS.md` §10 verification gate to point to `scripts/verify.sh`.

### Out of scope

- Writing new content beyond placeholders.
- Translations.

## Deliverables

Site configuration, scripts, workflows, placeholder folders.

## Acceptance criteria

- [ ] AC-1 `scripts/verify.sh` passes locally and in CI.
- [ ] AC-2 The site builds with every existing page reachable from the navigation, and Mermaid diagrams render.
- [ ] AC-3 Links between documents still work when browsing the repository on GitHub (no site-only link syntax).
- [ ] AC-4 A deliberately broken relative link and a deliberate misspelling each make CI fail.
- [ ] AC-5 Pages deployment workflow is ready (the owner may need to enable Pages; if so, list it under open questions).

## Verification

`scripts/verify.sh`; CI runs for failing and passing cases; screenshot or link of the built site.

## Notes and pitfalls

Relative links with `.md` extensions work on both GitHub and mdBook; avoid absolute site paths.

## Escalate if

A tool's only suitable release is younger than 24 hours.
