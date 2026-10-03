# CORE-008: Font audit and bundled-library proposal

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | TEXT |
| Repository | bayan-core (`lab/`) and docs |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | CORE-003; LAB-002 (reference machine with Microsoft fonts); LAB-001 feature tags for font frequencies |
| Unblocks | CORE-110 (font system), font gap programme |
| Status | Ready |
| Requirements | FID-02, FID-05, FID-07 |
| Decisions | ADR-0010, ADR-0009, ADR-0017 (licenses) |
| Specs | [font-compatibility.md](../../specs/font-compatibility.md) |

## Context

The font compatibility table was compiled from public sources and must be verified by measurement. Fonts are the largest single fidelity risk (R-02), above all Aptos. Microsoft's font files may be used on the reference machine under its license, but must never leave it; only derived comparison statistics may.

## Objective

Measured verification of every substitute in the font compatibility table, corpus font frequencies, and a concrete proposal for the bundled font library and the gap programme.

## Scope

### In scope

- A font comparison tool in `lab/` that compares two font files: advance widths for all mapped code points, vertical metrics (`head` units per em, `hhea`, `OS/2` typo and Windows ascent/descent, line gap), kerning results for frequent pairs via shaping, and glyph coverage. Output: summary statistics and lists of differing code points with deltas; never full metric tables of Microsoft fonts.
- Run it on the reference machine for every row of the table (including Aptos and its variants, Calibri Light, Cambria Math) against candidate substitutes.
- Font frequency analysis over the public and (aggregate only) private corpora: which families, styles and scripts appear how often.
- A proposal: bundled set (file, version, license, size, SHA-256), mapping table from Microsoft family names to substitutes, fallback chain per script, symbol-font mapping plan, delivery plan (desktop core set versus optional packs; web chunking), and a ranked gap list with recommended action and rough cost.
- Legal-review flags for any font that copies metrics or kerning (for example the early Aptos-compatible project noted in the table).
- Update `specs/font-compatibility.md` to v1 via a docs pull request.

### Out of scope

Implementing the font system (CORE-110); commissioning fonts.

## Deliverables

Comparison tool, measurement report, frequency report, docs pull request with spec v1 and the proposal.

## Acceptance criteria

- [ ] AC-1 Every row of the compatibility table has a measured status (compatible, partially compatible with listed differences, or gap).
- [ ] AC-2 The proposal lists total sizes and licenses, and every bundled font is on the ADR-0017/ADR-0010 license list.
- [ ] AC-3 The gap list is ranked by measured corpus frequency.
- [ ] AC-4 No Microsoft font file or full metric table appears in any repository or artifact (reviewer checks).

## Verification

Tool tests on open fonts in CI; reference-machine run logs summarized in the pull request.

## Escalate if

Licensing of a candidate font is unclear, or the measurements contradict ADR-0010's assumptions (for example a "metric-compatible" font that is not).
