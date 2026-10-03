# Font Compatibility — v0

- **Status:** v0, compiled from public sources on 2026-10-03. CORE-008 verifies every row by measurement (advance widths, vertical metrics, kerning) against the real fonts on the Word reference machine and promotes this to v1.
- **Owner stream:** TEXT
- **Related:** ADR-0010, CORE-008, CORE-110

## 1. Why this matters

Word breaks lines using glyph advance widths. A substitute font with even slightly different widths reflows every paragraph. A **metric-compatible** font has identical advance widths (and ideally identical vertical metrics and kerning) to the original, so lines and pages break identically even though the letterforms look different.

What must match, in order of impact:

1. **Advance widths** of every glyph used (decides line breaks).
2. **Vertical metrics** Word uses for line height (which values Word reads from the OS/2 and hhea tables is itself a Word Behavior Note to establish).
3. **Kerning** (only matters when the document enables kerning).
4. **Glyph coverage** (missing glyphs trigger fallback fonts with different widths).

## 2. Word's default fonts over time

| Word version | Body / headings default |
|---|---|
| Word 2003 and earlier | Times New Roman 12 pt |
| Word 2007 to 2023 | Calibri 11 pt body; Cambria (2007–2010) then Calibri Light (2013+) headings |
| Microsoft 365 since the theme change (rolled out December 2023 – March 2024) | **Aptos** body, Aptos Display headings |

Documents in the wild therefore cluster around Times New Roman, Calibri and, increasingly, Aptos.

## 3. Microsoft fonts and open substitutes

| Microsoft font | Open substitute | License | Compatibility notes | Status |
|---|---|---|---|---|
| Arial | Liberation Sans 2.1.5; Arimo | OFL-1.1; Arimo listed as OFL-1.1 by Google Fonts | Metric-compatible | Verify |
| Times New Roman | Liberation Serif 2.1.5; Tinos | OFL-1.1 | Metric-compatible | Verify |
| Courier New | Liberation Mono 2.1.5; Cousine | OFL-1.1 | Metric-compatible | Verify |
| Calibri | Carlito | OFL-1.1 | Regular, Italic, Bold, Bold Italic only; **no Light** | Verify |
| Calibri Light | — | — | **Gap** (common for headings 2013–2023) | Gap |
| Cambria | Caladea | OFL-1.1 | Metric-compatible | Verify |
| Cambria Math | — | — | **Gap**; math layout also depends on the OpenType MATH table | Gap |
| Georgia | Gelasio | OFL-1.1 | Metric-compatible in four styles | Verify |
| Segoe UI | Selawik (Microsoft) | OFL-1.1 | Five upright weights, no italics; **kerning differs** | Verify |
| Arial Narrow | Liberation Sans Narrow 1.07 | GPLv2 with font exception (older Liberation 1.x only) | License needs review before bundling | Review |
| Consolas | "DMCA Sans Serif" | Public domain | Same metrics claimed; small project | Verify |
| Tahoma | Wine's Tahoma | LGPL | From the Wine project | Verify |
| Century Gothic | URW Gothic; TeX Gyre Adventor | AGPL-3.0 with font exception (URW); GUST Font License (TeX Gyre) | Century Gothic was drawn to ITC Avant Garde widths | Verify |
| Book Antiqua / Palatino Linotype | TeX Gyre Pagella; URW P052 | GUST; AGPL-3.0 with font exception | Palatino metrics | Verify |
| Century Schoolbook | TeX Gyre Schola; URW C059 | GUST; AGPL-3.0 with font exception | | Verify |
| Verdana, Trebuchet MS, Garamond | — | — | **Gap** | Gap |
| **Aptos** (and Aptos Display, Narrow, Serif, Mono) | — (an early OFL project, "Intos", claims Aptos metric compatibility; derived from Inter and Gelasio; no releases; copies metrics and kerning) | — | **Gap; highest priority.** Aptos is a free download for users but may not be redistributed | Gap |
| Symbol, Wingdings 1–3, Webdings | Mapping of their private-use code points (U+F020–U+F0FF) to Unicode or OpenSymbol glyphs; LibreOffice's MPL-2.0 conversion tables are a starting point | MPL-2.0 (tables, OpenSymbol to verify) | Not metric-compatible, but bullets and symbols are mostly isolated glyphs | Verify |
| Segoe UI Emoji | Noto Color Emoji | OFL-1.1 | Different metrics; emoji-heavy lines may differ | Accept |

Bundling rule (ADR-0010): only fonts with licenses on the allowlist, shipped as separate data with their license files. AGPL-with-font-exception fonts need a specific license review before bundling.

## 4. East Asian and complex-script defaults

These are typical Office defaults for East Asian and complex scripts; exact defaults depend on the theme, Office version and language settings (CORE-008 confirms).

| Script | Common Word defaults | Open fallback | Notes |
|---|---|---|---|
| Japanese | Yu Mincho / Yu Gothic (newer), MS Mincho / MS Gothic (older) | Noto Serif/Sans CJK JP | No metric-compatible clones. Most ideographs are full-width (one em), so line breaks often survive; Latin and kana in these fonts differ |
| Chinese (Simplified) | DengXian (newer), SimSun (older) | Noto Sans/Serif CJK SC | Same as above |
| Chinese (Traditional) | PMingLiU, Microsoft JhengHei | Noto Sans/Serif CJK TC | Same as above |
| Korean | Malgun Gothic | Noto Sans/Serif CJK KR | Same as above |
| Arabic, Hebrew | Times New Roman, Arial and other system fonts for complex scripts | Noto Naskh Arabic, Noto Sans Arabic, Noto Sans/Serif Hebrew | Arabic text in Times New Roman or Arial is covered by Liberation only if Liberation's coverage matches; verify |
| Indic, Thai, others | Platform fonts (Nirmala UI, Leelawadee UI, …) | Noto families | No metric clones |

## 5. Gap programme

Ranked by expected corpus impact (CORE-008 replaces this ranking with measured frequencies):

1. **Aptos family**: evaluate existing open efforts after legal review; otherwise commission an OFL design with matching metrics. Funding needed.
2. **Calibri Light**: extend Carlito or commission.
3. **Cambria Math**: study how much math layout depends on its metrics; choose STIX Two Math or Latin Modern Math as interim with a fidelity warning.
4. **Verdana, Trebuchet MS, Garamond, Arial Narrow**: assess corpus frequency first.
5. **East Asian fonts**: measure how often line breaks actually differ with Noto CJK before investing.

Every font that copies another's metrics or kerning receives legal review before it ships.
