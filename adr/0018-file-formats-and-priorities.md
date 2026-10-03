# ADR-0018: File formats and conversion priorities

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** FMT-01…FMT-12, FID-01, FID-03, FID-10, ADR-0007, [specs/coverage-matrix.md](../specs/coverage-matrix.md)

## Context

Users live in `.docx`, but they also receive legacy `.doc`, move rich text through the clipboard as RTF and HTML, exchange `.odt` with public administrations, and need PDF in several conformance levels. All format specifications we rely on are public: ECMA-376 5th edition (Part 1 2016, Part 2 2021, Part 3 2015, Part 4 2016) and ISO/IEC 29500 (a new edition of Part 1 reached the final draft stage in March 2026), plus Microsoft's [MS-DOCX], [MS-DOC], [MS-OVBA] and [MS-OFFCRYPTO], all covered by Microsoft's Open Specification Promise (which covers patent claims necessary to implement the required parts of those specifications).

## Decision

### Priorities

| Format | Read | Write | Phase |
|---|---|---|---|
| `.docx`, `.dotx`, `.docm`, `.dotm` (Transitional and Strict) | Yes | Yes (Transitional) | Read P1, write P2 |
| Password-encrypted Word files (Agile Encryption) | Yes | Yes | P2 |
| RTF (files and clipboard) | Yes | Yes | P2 |
| HTML | Paste P2, files P4 | Clipboard P2, files P4 | P2 / P4 |
| Plain text | Yes | Yes | P2 |
| Markdown | Yes | Yes | P2 / P4 |
| PDF | Reflow import P6 (could) | Basic P1; PDF/A-2b and tagged P2; PDF/X-4, X-1a, validated PDF/A and PDF/UA P4 | P1–P6 |
| `.doc` (Word 97–2003) | Yes | Later "could" | P4 |
| `.odt` | Yes | Yes | P4 |
| EPUB 3 | — | Yes | P5 |

### Rules for writing OOXML

1. **Write Transitional OOXML** (what Word writes by default) for maximum compatibility; read both Transitional and Strict.
2. **Never upgrade a document's compatibility mode** without explicit user action.
3. **Untouched content is written verbatim:** untouched parts byte-for-byte, untouched paragraphs and tables from their source spans; regenerated elements re-attach preserved unknown children.
4. **BayanDocs-specific data** (layout epoch, font set, bleed and slug, enhanced typography settings) lives in a dedicated namespace (`http://schemas.bayandocs.org/…`) declared in `mc:Ignorable`, or in custom parts with BayanDocs relationship types. We never invent elements or attributes in Microsoft namespaces.
5. When BayanDocs edits an object stored as `mc:AlternateContent`, it regenerates the choice it understands and drops a stale fallback rather than emitting inconsistent fallbacks; this is verified in the lab against current Word.
6. Generated identifiers (paragraph IDs, revision IDs, relationship IDs) are unique and stable across saves where Word expects stability.

## Consequences

- The `.docx` family dominates Phase 1–2 effort; other formats follow once the model is mature.
- Clipboard interoperability requires RTF and HTML early (Phase 2), even before `.odt` and `.doc` files.

## Alternatives considered

- **Native BayanDocs file format:** rejected; `.docx` is the interchange format users need, and our extensions fit inside it.
- **Writing Strict OOXML:** cleaner, but less compatible with existing tools and Word's defaults.

## Revisit when

Corpus or user data shows a format's real-world share differs from these assumptions (for example, heavy `.doc` use in a target market).
