# Phase 1 — Faithful Viewer: core work packages (drafts)

**Status: Draft.** These are scoped and ordered but will be refined into individual Ready briefs (using [TEMPLATE.md](../TEMPLATE.md)) at the Phase-0 gate, because the spikes (CORE-003, CORE-004, LAB-005, DESK-002, WEB-002, SRV-002) may change them. All are in bayan-core; attach bayan-core and docs.

Phase-1 goal: open common `.docx` files and lay them out like Word, render them identically everywhere, export PDF, and re-save losslessly. See [plan/04-roadmap.md](../../plan/04-roadmap.md#phase-1--faithful-viewer) for exit criteria.

**Critical path:** CORE-101 → CORE-102/103/105 → CORE-108 → CORE-110/111/112 → CORE-113 → CORE-115/116 → CORE-121 → CORE-125.

## Model and import

### CORE-101 — Document model v1
- **Size:** L · **Depends on:** CORE-004 · **Decisions:** ADR-0007, ADR-0008 · **Requirements:** FID-03, COL-01
- **Objective:** production `bayan-crdt` and `bayan-model` covering every entity in the document model spec (stories, atoms, marks, paragraph properties, tables, objects, notes, comments, fields, ranges, global parts), normalization, change sets and derived views; promote the spec to v1.
- **Exit evidence:** convergence and normalization property tests; complete API documentation; spec v1 merged in docs.

### CORE-102 — DOCX import: body content
- **Size:** L · **Depends on:** CORE-101, CORE-005, CORE-006 · **Decisions:** ADR-0007, ADR-0018
- **Scope:** paragraphs, runs and every run-content element; text sanitization (WBN-0011); hyperlinks; bookmarks; complex and simple fields; inline and block content controls; revision containers; comment anchors; custom XML and smart-tag elements (preserved); unknown content preserved; source spans; `lastRenderedPageBreak` diagnostics table.
- **Exit evidence:** every public-corpus document imports without error; preservation tests; fuzz target running in CI.

### CORE-103 — DOCX import: styles, defaults, theme, settings, fonts
- **Size:** M · **Depends on:** CORE-101, CORE-006
- **Scope:** `styles.xml` (document defaults, latent styles, all style types), theme, `settings.xml` as typed fields for everything layout-affecting (including every compatibility option) plus preserved remainder, `fontTable.xml` with embedded-font de-obfuscation, web settings preserved.
- **Exit evidence:** list of typed settings versus the standard; round-trip tests.

### CORE-104 — DOCX import: numbering
- **Size:** S · **Depends on:** CORE-101, CORE-006
- **Scope:** abstract numbering, instances, level overrides, picture bullets, numbering styles.

### CORE-105 — DOCX import: tables, sections, headers and footers, notes, comments
- **Size:** M · **Depends on:** CORE-102
- **Scope:** all table, row and cell properties and merges; section properties; header and footer parts and their references; footnotes and endnotes including separator notes; comments with their extension parts (threads, done state, durable IDs, people).

### CORE-106 — DOCX import: drawings
- **Size:** L · **Depends on:** CORE-102
- **Scope:** DrawingML inline and anchored objects (pictures, shapes, groups, canvases, text boxes); legacy VML mapped to the same objects with originals preserved; `mc:AlternateContent` policy; charts, SmartArt, OLE objects and ink as objects with their caches and preview images; content-addressed media store.

### CORE-107 — Lossless export and verbatim pass-through
- **Size:** L · **Depends on:** CORE-102…CORE-106 · **Decisions:** ADR-0004 (Tier B), ADR-0018
- **Scope:** OOXML writer from the model; raw copy of untouched parts; verbatim untouched paragraphs and tables from source spans; regeneration of dirty elements with preserved children; namespace management; identifier uniqueness.
- **Exit evidence:** Tier B gate passing on the public corpus; Word re-open check via LAB-108.

### CORE-108 — Style cascade engine
- **Size:** M · **Depends on:** CORE-103, CORE-104
- **Scope:** effective run, paragraph, table, row and cell properties from defaults, table styles (with conditional formatting and table look), numbering, paragraph and character styles and direct formatting; toggle-property semantics; theme fonts and colors; caching and incremental invalidation.

### CORE-109 — Numbering engine
- **Size:** M · **Depends on:** CORE-108
- **Scope:** list labels for every number format Word supports (including ordinal and cardinal text in the main languages, alphabetic systems for Hebrew and Arabic, East Asian counting systems), restart and override logic, legal numbering, level text, suffixes, bullets through the symbol-font mapping.

## Text and fonts

### CORE-110 — Font system v1
- **Size:** M · **Depends on:** CORE-008, CORE-103 · **Decisions:** ADR-0010
- **Scope:** bundled library from CORE-008; resolution order; host font provider; embedded fonts; font hashing and reporting; machine-dependence flags; per-script fallback chains; caches.

### CORE-111 — Text pipeline v1
- **Size:** L · **Depends on:** CORE-003, CORE-110, LAB-005 · **Decisions:** ADR-0009
- **Scope:** itemization by Word's font slots (ASCII, high ANSI, East Asian, complex script) and hint rules; shaping cache; the Word measurement model from WBN-0001 to WBN-0003 and later notes; OpenType features applied as Word applies them.

### CORE-112 — Line breaking, justification, tabs and bidi
- **Size:** L · **Depends on:** CORE-111, LAB-102
- **Scope:** Word-tailored line breaking; East Asian rules; automatic spacing between Asian and Latin text; justification modes; tab stops of every kind with leaders and positional tabs; bidirectional reordering; WBN-0004 to WBN-0006.

## Layout

### CORE-113 — Paragraph layout and pagination core
- **Size:** L · **Depends on:** CORE-112, CORE-108
- **Scope:** indents, spacing (including contextual and automatic spacing), line spacing, borders and shading with merging, drop caps and frames; keep-with-next, keep-lines-together, widow and orphan control; page and column flow; **incremental re-pagination** that stops when page boundaries realign; layout tree in BLU; `bayan-cli` layout JSON dump for the lab.

### CORE-114 — Headers, footers and page numbering
- **Size:** M · **Depends on:** CORE-113
- **Scope:** first, even and default headers and footers with inheritance across sections; header and footer growth into the body; page number formats and restarts; watermarks.

### CORE-115 — Table layout v1
- **Size:** L · **Depends on:** CORE-113, LAB-103
- **Scope:** fixed layout and the autofit algorithm (WBN-0007); cell margins and spacing; border conflict resolution; merges; row height rules; rows splitting across pages; repeated header rows; nested and floating tables; right-to-left tables; cell text direction and vertical alignment.

### CORE-116 — Floating objects and text wrapping
- **Size:** L · **Depends on:** CORE-113, LAB-104
- **Scope:** anchor positioning for every reference frame; wrap modes and polygons; z-order and overlap; layout in table cells; positioned paragraphs and frames; WBN-0008.

### CORE-117 — Footnotes and endnotes layout
- **Size:** M · **Depends on:** CORE-113, LAB-105
- **Scope:** placement, separators and continuation, numbering formats and restarts, endnotes at section or document end; interaction with pagination (WBN-0009).

### CORE-118 — Columns and section breaks
- **Size:** M · **Depends on:** CORE-113
- **Scope:** equal and unequal columns, separators, column breaks, column balancing at continuous section breaks, section break types including even and odd pages.

### CORE-119 — Fields v1
- **Size:** M · **Depends on:** CORE-113
- **Scope:** field-code parser with all switches; evaluation of page, date, document-information and sequence fields; cached results for everything else; table-of-contents display from cached results; external and active fields never refreshed (CORE-130).

### CORE-120 — Comments and tracked-changes display
- **Size:** M · **Depends on:** CORE-113
- **Scope:** inline revision markup; comment indicators; the four markup views (simple, all, none, original). Balloons in the margin follow in Phase 2.

## Rendering and output

### CORE-121 — Display list and reference rasterizer v1
- **Size:** L · **Depends on:** CORE-003, CORE-113 · **Decisions:** ADR-0011
- **Scope:** production `bayan-render` and `bayan-raster` from the spike; every border style; tiling and caching; interactive mode if recommended by CORE-003; `bayan-cli` PNG rendering.

### CORE-122 — Images and DrawingML rendering v1
- **Size:** L · **Depends on:** CORE-106, CORE-121
- **Scope:** pure-Rust image decoders with limits; all preset geometries; fills (solid, gradient, pattern, picture); lines and arrowheads; basic effects; text in shapes; SVG through resvg.

### CORE-123 — EMF, WMF and EMF+ renderer
- **Size:** L · **Depends on:** CORE-121
- **Scope:** evaluate existing pure-Rust crates (for example emfsdk, emf-core/wmf-core); contribute upstream or write our own; render to the display list; fuzzing.

### CORE-124 — PDF export v1
- **Size:** M · **Depends on:** CORE-121 · **Decisions:** ADR-0011
- **Scope:** krilla-based export with subset fonts, links, outline from headings, metadata, basic structure tags; groundwork for PDF/A-2b; `bayan-cli` conversion command; veraPDF syntax validation in CI.

### CORE-125 — Engine API v1 for viewing
- **Size:** L · **Depends on:** CORE-007, CORE-121 · **Decisions:** ADR-0012
- **Scope:** protocol v1: opening real documents with prompts (passwords later, external content consent), page information, tiles, read-only selection overlays, find, outline, copy as plain text and HTML, accessibility tree, record and replay; published JSON Schema and TypeScript declarations; first tagged core release consumed by both shells.

### CORE-126 — Equation (OMML) rendering v1
- **Size:** L · **Depends on:** CORE-111, CORE-121
- **Scope:** OpenType MATH-table-based layout of OMML structures with the interim open math font; documented fidelity limits (Cambria Math gap).

### CORE-127 — Chart and SmartArt rendering v1
- **Size:** L · **Depends on:** CORE-122
- **Scope:** bar, column, line, pie, area, scatter and combination charts from cached data; SmartArt from Word's stored drawing cache.

### CORE-128 — Accessibility tree v1
- **Size:** M · **Depends on:** CORE-113 · **Decisions:** ADR-0020
- **Scope:** `bayan-a11y`: headings, paragraphs, lists, tables with headers, links, images with alternative text, comments and revisions, reading order, incremental updates.

## Quality and security

### CORE-129 — Performance and memory budgets
- **Size:** M · **Depends on:** CORE-113, CORE-121
- **Scope:** reference document set; benchmarks for PERF-02, PERF-03, PERF-05 and PERF-06; incremental-layout hardening; nightly performance gate with stored baselines.

### CORE-130 — Active-content blocking and malicious-sample suite
- **Size:** M · **Depends on:** CORE-102, CORE-106 · **Decisions:** ADR-0023
- **Scope:** detection and blocking of every vector in the plan's document-borne threat table; consent prompts through the protocol; a synthetic malicious-sample corpus run in CI.
