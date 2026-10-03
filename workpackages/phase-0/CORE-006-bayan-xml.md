# CORE-006: `bayan-xml` — Markup-Compatibility-aware XML with lossless preservation

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | FORMATS |
| Repository | bayan-core |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | CORE-001 |
| Unblocks | CORE-102…CORE-107 |
| Status | Ready |
| Requirements | FID-01, FID-03, SEC-01 |
| Decisions | ADR-0006, ADR-0007 (§2–3 preservation and source spans), ADR-0018 |
| Specs | [document-model.md §13](../../specs/document-model.md#13-preservation-and-source-spans) |

## Context

WordprocessingML relies on namespaces (dozens of Microsoft extension namespaces) and on Markup Compatibility and Extensibility (ECMA-376 Part 3: `mc:Ignorable`, `mc:AlternateContent`, `mc:ProcessContent`, `mc:MustUnderstand`). Lossless round-trip requires capturing unknown content exactly and writing untouched elements verbatim. `quick-xml` is the planned base (versions from 0.41 fix two 2026 denial-of-service advisories).

## Objective

An XML layer that parses OOXML parts safely, applies Markup Compatibility rules correctly, captures unknown content losslessly (both as verbatim source spans and as re-serializable fragments), and writes XML deterministically.

## Scope

### In scope

- Streaming reader on `quick-xml` (pinned, at least 0.41) that rejects document type declarations and external entities, supports only predefined and character entities, and enforces limits on depth, attribute count, name length and total size.
- Namespace resolution with a table of known OOXML namespaces (WordprocessingML and its 2010–2023 extensions, relationships, DrawingML families, VML, Office, Math, Markup Compatibility, packaging), including the mapping between Strict and Transitional namespace URIs.
- Markup Compatibility processing per ECMA-376 Part 3: ignorable namespaces not understood are skipped for interpretation but preserved; `AlternateContent` selects the first `Choice` whose `Requires` namespaces are understood, else `Fallback`, while preserving the whole element for round-trip; `ProcessContent`, `MustUnderstand` (error if not understood), `PreserveElements`/`PreserveAttributes`.
- Lossless capture: (a) byte ranges of elements in the source part (source spans) and (b) re-serializable fragments carrying the namespace declarations they need, so a fragment can be emitted into a different context.
- Deterministic writer with namespace management, correct escaping, `xml:space="preserve"` handling, stable attribute order for generated content, and verbatim emission of source spans.
- Fuzz targets for the reader and for the Markup Compatibility processor.
- Tests: real WordprocessingML snippets, the Markup Compatibility examples from the standard, Strict-namespace documents.

### Out of scope

WordprocessingML semantics (CORE-102 onward).

## Deliverables

The `bayan-xml` crate, fuzz targets, tests, documentation.

## Acceptance criteria

- [ ] AC-1 Parse-then-write of sample parts is semantically identical under a canonical comparison, and verbatim spans are byte-identical.
- [ ] AC-2 Markup Compatibility test cases (from the standard's examples plus our own) pass, including nested `AlternateContent`.
- [ ] AC-3 Documents containing a DTD or external entity are rejected; entity-expansion attacks are impossible by construction (test).
- [ ] AC-4 Fuzz targets ran for at least one CPU-hour without crashes.
- [ ] AC-5 No `unsafe`; dependencies justified.

## Verification

`cargo xtask verify`; fuzz durations recorded.

## Escalate if

`quick-xml` cannot provide exact source offsets needed for verbatim spans; propose an alternative.
