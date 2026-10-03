# ADR-0010: Font strategy and the bundled font library

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** FID-02, FID-05, FID-07, ADR-0004, ADR-0009, [specs/font-compatibility.md](../specs/font-compatibility.md), CORE-008, CORE-110

## Context

Line breaks depend on glyph advance widths. If a document asks for Calibri and we render with a font of different widths, every paragraph reflows. Microsoft's fonts cannot be redistributed. Open **metric-compatible** fonts exist for several of them (identical advance widths, so line breaks match even though letterforms differ): Liberation (Arial, Times New Roman, Courier New), Carlito (Calibri, but no Light weight), Caladea (Cambria), Gelasio (Georgia), Selawik (Segoe UI, but kerning differs). Others have **no open equivalent**, most importantly **Aptos**, Word's default font since the theme change rolled out between December 2023 and March 2024. Aptos is a free download for users but may not be redistributed. No established open metric-compatible Aptos exists as of 2026-10-03 (one early OFL project, Intos, claims compatibility and copies Aptos metrics and kerning; it needs legal and quality review). Cambria Math, Verdana, Trebuchet MS and Garamond also lack equivalents. Word honors fonts embedded in documents.

## Decision

1. **Font resolution order** for each requested family, style and script:
   1. fonts **embedded in the document** (de-obfuscated per ECMA-376; embedding permissions honored for editing and re-saving);
   2. the **organization font library** served by the self-hosted server (content-hashed);
   3. the **BayanDocs bundled library**: metric-compatible substitutes mapped from Microsoft family names, plus broad-coverage fallbacks (Noto families) for scripts and symbols;
   4. **fonts installed on the user's system**, only when 1–3 cannot provide the family; the document is then flagged machine-dependent (ADR-0004);
   5. a last-resort substitute chosen deterministically from font classification data, with a visible warning.
2. **For families with a verified metric-compatible substitute, layout always uses the substitute**, even if the real font is installed, so that layout is identical on every machine. A per-user option "prefer installed fonts" exists, and turning it on marks the user's view as machine-dependent.
3. **Every font is identified by the SHA-256 of its file.** The engine reports which font files a layout used; documents saved by BayanDocs record their font set in an ignorable extension so mismatches between machines are detectable.
4. **Reverse fidelity:** when a document uses a family that only BayanDocs bundles (for example our default font), saving embeds a subset of that open font (obfuscated as the specification requires) so Word users see the same layout.
5. **Symbol fonts:** bullets and symbols in Symbol, Wingdings and Webdings private-use code points are mapped to equivalent glyphs through a mapping table. LibreOffice's MPL-2.0 conversion tables are a permitted, attributed starting point; gaps are tracked.
6. **Gap programme** (owned by CORE-008 and later font work packages): for each high-impact family without an open equivalent (Aptos first, then Cambria Math, Calibri Light, Verdana, Trebuchet MS, Garamond, Arial Narrow and East Asian defaults), choose among commissioning an OFL metric-compatible design, contributing to an existing open project, or documented substitution. Any font that copies another font's metrics or kerning gets legal review before it ships.
7. **Delivery:** desktop installers include the core Latin/Greek/Cyrillic/Arabic/Hebrew set; large East Asian fonts are optional packs downloaded on demand with hash verification. The web loads fonts lazily in Unicode-range chunks with integrity hashes; layout of affected paragraphs waits for required fonts rather than reflowing after a placeholder.
8. **Licensing of bundled fonts:** SIL OFL 1.1, Apache-2.0, GUST Font License, public domain, or LGPL with font exceptions are acceptable for bundling as separate data; each font's license ships alongside it.

## Consequences

- Determinism holds wherever bundled, embedded or organization fonts suffice, which covers most documents.
- Documents defaulting to Aptos remain the main fidelity gap until the gap programme delivers; the Fidelity Inspector makes the gap visible to users.
- Bundled fonts add tens of megabytes to desktop installers (East Asian packs excluded) and lazy downloads on the web.

## Alternatives considered

- **Use system fonts first:** better looks on machines that have them, but breaks determinism across machines.
- **Bundle proprietary fonts:** illegal.
- **Always substitute visually similar fonts:** reflows documents; rejected.

## Revisit when

An open metric-compatible Aptos becomes available and passes legal review; Microsoft changes Word's default font again; or the corpus shows a different font driving most fidelity failures.
