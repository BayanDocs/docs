# Word Feature Coverage Matrix — v1

- **Status:** v1 (planning baseline). Each row's **Status** is updated by the work package that implements it; the Fidelity Lab's feature tags use the same names.
- **Columns:** *Display* = phase in which BayanDocs lays out and renders the feature faithfully (viewer); *Edit* = phase in which it can be created and modified; *Pri* = P0 (essential for most documents) to P3 (rare). Status values: — (not started), Partial, Done, Preserved (kept and written back but not rendered).
- Priorities will be recalibrated from measured corpus frequencies at the Phase-0 gate (LAB-001 feature tagging).

## Package and document structure

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| OPC package, content types, relationships | `[Content_Types].xml`, `_rels` | P1 | P2 | P0 | — |
| Markup Compatibility (AlternateContent, Ignorable) | `mc:*` | P1 | P2 | P0 | — |
| Strict OOXML namespace variant | Strict namespaces | P1 | — (write Transitional) | P2 | — |
| Unknown parts and extensions preserved | any | P1 (Preserved) | — | P0 | — |
| Core, app and custom properties | `docProps/*` | P1 | P2 | P1 | — |
| Custom XML parts | `customXml/*` | P1 (Preserved) | P4 | P2 | — |
| Glossary document (building blocks) | `word/glossary/*` | P1 (Preserved) | P2 | P2 | — |
| Embedded fonts | `w:embedRegular` etc. | P1 | P2 (write) | P1 | — |
| Password encryption (Agile) | MS-OFFCRYPTO | P2 | P2 | P1 | — |
| Digital signatures | `_xmlsignatures/*` | P1 (Preserved) | P4 | P2 | — |
| VBA project | `vbaProject.bin` | P1 (Preserved) | P4 (view) | P2 | — |

## Characters and runs

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Text, tabs, breaks, symbols | `w:t`, `w:tab`, `w:br`, `w:cr`, `w:sym` | P1 | P2 | P0 | — |
| Fonts per script slot and hints | `w:rFonts` (ascii, hAnsi, eastAsia, cs, hint, theme fonts) | P1 | P2 | P0 | — |
| Size, bold, italic (incl. complex-script variants) | `w:sz`, `w:szCs`, `w:b`, `w:bCs`, `w:i`, `w:iCs` | P1 | P2 | P0 | — |
| Underline styles and colors | `w:u` | P1 | P2 | P0 | — |
| Strike, double strike, caps, small caps, hidden | `w:strike`, `w:dstrike`, `w:caps`, `w:smallCaps`, `w:vanish` | P1 | P2 | P0 | — |
| Color (incl. theme colors, tint, shade) | `w:color` | P1 | P2 | P0 | — |
| Highlight and shading | `w:highlight`, `w:shd` | P1 | P2 | P0 | — |
| Superscript, subscript, position | `w:vertAlign`, `w:position` | P1 | P2 | P0 | — |
| Character spacing, scaling, kerning threshold | `w:spacing`, `w:w`, `w:kern` | P1 | P2 | P1 | — |
| Borders around text | `w:bdr` | P1 | P2 | P2 | — |
| Emphasis marks, East Asian layout options | `w:em`, `w:eastAsianLayout` | P2 | P4 | P2 | — |
| Fit text | `w:fitText` | P2 | P4 | P3 | — |
| Language tags | `w:lang` | P1 | P2 | P0 | — |
| Right-to-left and complex-script flags | `w:rtl`, `w:cs` | P1 | P2 | P0 | — |
| Text effects (glow, shadow, outline, reflection, fill) | `w14:glow`, `w14:shadow`, `w14:textOutline`, `w14:textFill`, … | P2 | P5 | P2 | — |
| OpenType features | `w14:ligatures`, `w14:numForm`, `w14:numSpacing`, `w14:stylisticSets`, `w14:cntxtAlts` | P1 | P4 | P1 | — |
| Hyperlinks | `w:hyperlink` | P1 | P2 | P0 | — |
| Ruby (phonetic guide) | `w:ruby` | P2 | P4 | P2 | — |

## Paragraphs

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Alignment (incl. distribute, Thai, kashida variants) | `w:jc` | P1 | P2 | P0 | — |
| Indentation (left, right, first line, hanging, chars) | `w:ind` | P1 | P2 | P0 | — |
| Spacing before/after, auto spacing, contextual spacing | `w:spacing`, `w:contextualSpacing` | P1 | P2 | P0 | — |
| Line spacing (auto, exact, at least) | `w:spacing/@line`, `@lineRule` | P1 | P2 | P0 | — |
| Tab stops (all alignments and leaders, bar tabs) | `w:tabs` | P1 | P2 | P0 | — |
| Keep with next, keep lines together, page break before, widow control | `w:keepNext`, `w:keepLines`, `w:pageBreakBefore`, `w:widowControl` | P1 | P2 | P0 | — |
| Paragraph borders and shading (with border merging) | `w:pBdr`, `w:shd` | P1 | P2 | P1 | — |
| Outline level | `w:outlineLvl` | P1 | P2 | P1 | — |
| Drop caps and frames | `w:framePr` | P1 | P2 | P2 | — |
| Bidirectional paragraphs | `w:bidi` | P1 | P2 | P0 | — |
| Snap to grid, East Asian line-breaking options | `w:snapToGrid`, `w:kinsoku`, `w:wordWrap`, `w:overflowPunct`, `w:topLinePunct`, `w:autoSpaceDE`, `w:autoSpaceDN` | P2 | P2 | P1 | — |
| Text alignment on line, text direction | `w:textAlignment`, `w:textDirection` | P2 | P4 | P2 | — |
| Suppress line numbers, suppress auto hyphens | `w:suppressLineNumbers`, `w:suppressAutoHyphens` | P1 | P2 | P2 | — |
| Paragraph mark formatting | `w:pPr/w:rPr` | P1 | P2 | P0 | — |

## Styles and themes

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Document defaults | `w:docDefaults` | P1 | P2 | P0 | — |
| Paragraph, character, linked styles and inheritance | `w:style` | P1 | P2 | P0 | — |
| Table styles with conditional formatting | `w:tblStylePr` | P1 | P2 | P0 | — |
| Numbering styles | `w:style w:type="numbering"` | P1 | P2 | P1 | — |
| Latent styles | `w:latentStyles` | P1 (Preserved) | P2 | P2 | — |
| Toggle properties semantics | ECMA-376 §17.7.3 | P1 | P2 | P0 | — |
| Theme fonts and colors | `theme1.xml`, `w:themeColor`, `w:asciiTheme`… | P1 | P2 | P0 | — |
| Style auto-redefinition (honored, but never silently) | `w:autoRedefine` | P2 | P2 | P2 | — |

## Numbering and lists

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Abstract numbering and instances, level overrides | `w:abstractNum`, `w:num`, `w:lvlOverride` | P1 | P2 | P0 | — |
| Number formats (decimal, roman, letters, ordinal, cardinal text, East Asian, Hebrew, Arabic and more) | `w:numFmt` | P1 | P2 | P0 | — |
| Level text, suffix, justification, legal numbering | `w:lvlText`, `w:suff`, `w:lvlJc`, `w:isLgl` | P1 | P2 | P0 | — |
| Restart rules | `w:lvlRestart`, `w:startOverride` | P1 | P2 | P0 | — |
| Picture bullets | `w:numPicBullet` | P1 | P4 | P2 | — |
| Legacy numbering | `w:legacy` | P2 | — | P3 | — |
| Heading outline numbering | numbering linked to heading styles | P1 | P2 | P0 | — |

## Sections and page layout

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Page size, orientation, margins, gutter | `w:pgSz`, `w:pgMar` | P1 | P2 | P0 | — |
| Section breaks (next page, continuous, even, odd) | `w:type` | P1 | P2 | P0 | — |
| Columns (equal, unequal, separator) and column balancing | `w:cols` | P1 | P2 | P0 | — |
| Vertical alignment of page | `w:vAlign` | P1 | P2 | P2 | — |
| Page borders (including art borders) | `w:pgBorders` | P1 (art: P4) | P2 | P2 | — |
| Line numbering | `w:lnNumType` | P1 | P2 | P2 | — |
| Page numbering format and restart | `w:pgNumType` | P1 | P2 | P0 | — |
| Document grid (East Asian) | `w:docGrid` | P2 | P2 | P1 | — |
| Text direction of section, right-to-left gutter | `w:textDirection`, `w:rtlGutter` | P2 | P4 | P2 | — |
| Mirror margins, book fold, gutter at top | settings | P1 | P2 | P2 | — |

## Headers and footers

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Default, first-page, even headers and footers | `w:headerReference`, `w:footerReference`, `w:titlePg`, `w:evenAndOddHeaders` | P1 | P2 | P0 | — |
| Link to previous (inheritance across sections) | implicit | P1 | P2 | P0 | — |
| Header/footer distances and growth into body | `w:pgMar/@header`, `@footer` | P1 | P2 | P0 | — |
| Watermarks (VML/WordArt in header) | `v:shape` in header | P1 | P2 | P1 | — |

## Tables

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Grid, widths, fixed layout | `w:tblGrid`, `w:tblW`, `w:tblLayout` | P1 | P2 | P0 | — |
| Autofit layout algorithm | `w:tblLayout w:type="autofit"` | P1 | P2 | P0 | — |
| Horizontal and vertical merges | `w:gridSpan`, `w:vMerge`, `w:hMerge` | P1 | P2 | P0 | — |
| Borders (with conflict resolution) and shading | `w:tblBorders`, `w:tcBorders`, `w:shd` | P1 | P2 | P0 | — |
| Cell margins and spacing | `w:tblCellMar`, `w:tcMar`, `w:tblCellSpacing` | P1 | P2 | P1 | — |
| Row height rules, cannot split, header rows | `w:trHeight`, `w:cantSplit`, `w:tblHeader` | P1 | P2 | P0 | — |
| Rows splitting across pages | — | P1 | — | P0 | — |
| Nested tables | `w:tc/w:tbl` | P1 | P2 | P1 | — |
| Floating tables | `w:tblpPr` | P1 | P2 | P1 | — |
| Right-to-left tables | `w:bidiVisual` | P1 | P2 | P1 | — |
| Cell text direction, vertical alignment | `w:textDirection`, `w:vAlign` | P1 | P2 | P1 | — |
| Table formulas | `=` fields | P2 | P2 | P2 | — |

## Fields

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Complex and simple fields, nesting | `w:fldChar`, `w:instrText`, `w:fldSimple` | P1 | P2 | P0 | — |
| Page fields | `PAGE`, `NUMPAGES`, `SECTIONPAGES`, `PAGEREF` | P1 | P2 | P0 | — |
| Date and time with picture switches and calendars | `DATE`, `TIME`, `CREATEDATE`, `SAVEDATE`, `PRINTDATE` | P1 | P2 | P0 | — |
| Cross-references and sequences | `REF`, `NOTEREF`, `SEQ`, `STYLEREF` | P1 (cached) / P2 (computed) | P2 | P0 | — |
| Document information | `AUTHOR`, `TITLE`, `FILENAME`, `DOCPROPERTY`, `DOCVARIABLE` | P1 | P2 | P1 | — |
| Tables of contents and figures | `TOC`, `TC` | P1 (cached) | P2 | P0 | — |
| Formulas and conditions | `=`, `IF`, `COMPARE` | P2 | P2 | P2 | — |
| Mail merge fields | `MERGEFIELD`, `NEXT`, `NEXTIF`, `SKIPIF`, `ASK`, `FILLIN` | P1 (cached) | P4 | P2 | — |
| Indexes and authorities | `XE`, `INDEX`, `TA`, `TOA` | P1 (cached) | P4 | P2 | — |
| Citations and bibliography | `CITATION`, `BIBLIOGRAPHY` | P1 (cached) | P4 | P1 | — |
| Legacy form fields | `FORMTEXT`, `FORMCHECKBOX`, `FORMDROPDOWN` | P1 | P4 | P2 | — |
| External and active fields (blocked by default) | `INCLUDETEXT`, `INCLUDEPICTURE`, `LINK`, `DDE`, `DDEAUTO` | P1 (cached, never refreshed) | — | P1 | — |
| Formatting switches | `\*`, `\#`, `\@`, `MERGEFORMAT` | P1 | P2 | P0 | — |

## Notes, comments and review

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Footnotes and endnotes (placement, numbering, separators, continuation) | `w:footnoteReference`, `w:footnotePr`, … | P1 | P2 | P0 | — |
| Comments with threads, resolution, people | `comments.xml`, `commentsExtended.xml`, `commentsIds.xml`, `commentsExtensible.xml`, `people.xml` | P1 | P2 | P0 | — |
| Tracked insertions and deletions | `w:ins`, `w:del` | P1 | P2 | P0 | — |
| Tracked moves | `w:moveFrom`, `w:moveTo` and ranges | P1 | P2 | P1 | — |
| Tracked formatting and property changes | `w:rPrChange`, `w:pPrChange`, `w:sectPrChange`, `w:tblPrChange`, … | P1 | P2 | P1 | — |
| Markup display modes and balloons | — | P1 (inline) / P2 (balloons) | P2 | P0 | — |
| Compare and combine documents | — | — | P4 | P1 | — |
| Restrict editing, permissions | `w:documentProtection`, `w:permStart/End` | P1 | P4 | P1 | — |

## Drawings and objects

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Inline and anchored pictures | `wp:inline`, `wp:anchor`, `pic:pic` | P1 | P2 | P0 | — |
| Image formats (PNG, JPEG, GIF, BMP, TIFF, WebP, SVG, EMF, WMF, EMF+) | `a:blip`, `asvg:svgBlip` | P1 | P2 | P0 | — |
| Cropping, recoloring, transparency, basic effects | `a:srcRect`, `a:duotone`, `a:alphaModFix`, … | P1 | P2 | P1 | — |
| Text wrapping (square, tight, through, top and bottom, behind, in front) | `wp:wrap*` | P1 | P2 | P0 | — |
| Positioning relative to page, margin, column, paragraph, line, character | `wp:positionH/V` | P1 | P2 | P0 | — |
| Shapes: preset and custom geometry, fills, lines, arrowheads | `wps:wsp`, `a:prstGeom`, `a:custGeom` | P1 | P2 | P1 | — |
| Text boxes and linked text boxes | `wps:txbx`, `w:txbxContent` | P1 | P2 | P0 | — |
| Groups and drawing canvases | `wpg:wgp`, `wpc:wpc` | P1 | P2 | P1 | — |
| Shape effects (shadow, glow, soft edges, 3D) | `a:effectLst`, `a:scene3d`, `a:sp3d` | P2 (3D: P6) | P5 | P2 | — |
| WordArt | `a:prstTxWarp`, VML text paths | P2 | P5 | P2 | — |
| Legacy VML shapes and pictures | `w:pict`, `v:*` | P1 | P2 | P1 | — |
| OLE objects (preview only; never activated) | `w:object`, `o:OLEObject` | P1 | — | P1 | — |
| Ink | `w14:contentPart` | P2 | P6 | P3 | — |
| 3D models | `am3d:*` | P2 (fallback image) | — | P3 | — |

## Equations, charts and diagrams

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Equations (OMML) | `m:oMath`, `m:oMathPara` | P1 | P4 | P1 | — |
| Legacy equations (Equation Editor 3, MathType as OLE with WMF preview) | OLE + WMF | P1 | — | P2 | — |
| Charts (bar, column, line, pie, area, scatter, combo) | `c:chartSpace` | P1 | P4 | P1 | — |
| Newer chart types (waterfall, treemap, sunburst, histogram, box and whisker, funnel, map) | `cx:chart` | P2 | P5 | P2 | — |
| 3D charts | `c:view3D` | P4 | P6 | P3 | — |
| SmartArt (from Word's drawing cache) | `dgm:*`, `dsp:*` | P1 | P5 | P1 | — |

## Content controls and forms

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Rich text, plain text, picture, checkbox, combo box, drop-down, date controls | `w:sdt` | P1 | P4 | P1 | — |
| Repeating sections, building block galleries | `w15:repeatingSection`, `w:docPartObj` | P1 | P4 | P2 | — |
| XML data binding | `w:dataBinding` | P1 (cached) | P4 | P2 | — |

## East Asian and complex scripts

| Feature | OOXML / behavior | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Arabic and Hebrew shaping and bidi | — | P1 | P2 | P0 | — |
| Kashida justification | `w:jc` kashida variants | P2 | P2 | P1 | — |
| Kinsoku (line-breaking rules) incl. custom lists | `w:kinsoku`, `w:noLineBreaksBefore/After` | P2 | P2 | P1 | — |
| Auto-spacing between Asian and Latin text and numbers | `w:autoSpaceDE`, `w:autoSpaceDN` | P2 | P2 | P1 | — |
| Character grid | `w:docGrid` | P2 | P2 | P1 | — |
| Vertical text | `w:textDirection` (tbRl, …) | P4 | P4 | P2 | — |
| Combine characters, two lines in one, enclosed characters | `w:eastAsianLayout` | P4 | P4 | P3 | — |
| Indic and Southeast Asian shaping and breaking | — | P1 | P2 | P1 | — |

## Compatibility settings

| Feature | OOXML | Display | Edit | Pri | Status |
|---|---|---|---|---|---|
| Compatibility mode 15 (Word 2013+) | `w:compatSetting compatibilityMode=15` | P1 | — | P0 | — |
| Compatibility modes 14, 12, 11 | same | P1 (14) / P2 (12, 11) | — | P1 | — |
| Individual legacy compatibility options (dozens) | `w:compat/*` | P1→P4 as found in corpus | — | P1–P3 | — |
