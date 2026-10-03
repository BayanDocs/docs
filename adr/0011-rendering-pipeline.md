# ADR-0011: Rendering pipeline — display lists, reference rasterizer, PDF

- **Status:** Accepted — validation gate (CORE-003)
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** FID-02, PUB-01…PUB-07, FMT-05, ADR-0004, ADR-0005, CORE-003, CORE-121, CORE-124

## Context

Pages must look identical on every platform (Tier A), print exactly, and export to PDF, PDF/A, PDF/UA and PDF/X. Ecosystem facts verified on 2026-10-03:

- **tiny-skia** 0.12 (BSD-3-Clause), a port of Skia's CPU rasterizer, stewarded by Linebender since 2024 and in maintenance mode. resvg reports identical pixels on x86 Windows and ARM macOS; its SIMD code admits NaN and signed-zero min/max differences between backends, and WebAssembly relaxed-SIMD results are implementation-defined.
- **vello_cpu** 0.3 (MIT/Apache-2.0, Linebender), first released July 2026, fast and actively developed. Its own tests allow ±1–2 per color channel between SIMD and scalar paths, so it is not bit-exact across platforms by default.
- **resvg/usvg** 0.48 renders SVG in pure Rust, using harfrust and skrifa for text.
- **krilla** 0.8 (MIT/Apache-2.0): high-level PDF writing with PDF/A-1 through PDF/A-4 variants, PDF/UA-1 and tagged PDF, font subsetting, CMYK through supplied ICC profiles, spot colors. It has **no PDF/X support** and writes only an sRGB output intent. **pdf-writer** is the low-level crate beneath it.
- **moxcms** (BSD-3-Clause or Apache-2.0) is a pure-Rust color management system used by `image`, Typst and hayro.

## Decision

1. **Layout produces a display list per page**: resolution-independent drawing commands (glyph runs with font hash and positions in BLU, paths, fills, strokes, images, clips, transforms, links and structure tags for accessibility). Display lists are the single input to every output backend.
2. **Reference rasterizer:** tiny-skia, pinned, with relaxed-SIMD disabled, used through `bayan-raster`. The reference mode must be **bit-exact across platforms**; CORE-003 verifies this, and if a SIMD path breaks bit-exactness the reference mode uses a single portable path on all targets.
3. **Interactive rasterizer:** CORE-003 benchmarks vello_cpu against tiny-skia. If adopted for on-screen rendering, it may differ from the reference by at most ±2 per color channel at anti-aliased edges and never in geometry; tests and exports always use the reference mode. GPU rendering is deferred to Phase 4.
4. **Glyphs** are rendered from skrifa outlines, unhinted, with grayscale anti-aliasing; no subpixel (ClearType-style) rendering, which is platform-dependent. Gamma and blending choices are fixed and documented by CORE-003.
5. **Overlays** that change often (caret, selection, remote cursors, find highlights) are described by the engine as geometry and drawn by the shells over the page tiles; spelling underlines and other document-plane marks are drawn by the engine.
6. **SVG images** render through resvg/usvg; scripts and external references in SVG are ignored.
7. **PDF:** krilla for PDF, PDF/A and tagged PDF/UA. **PDF/X-4 and X-1a** (output intents with CMYK ICC profiles, trim and bleed boxes, transparency rules) are built by us, preferably as upstream contributions to krilla, otherwise on pdf-writer. Color conversion uses moxcms (alternatives such as pure-Rust ports of LittleCMS are evaluated in Phase 4). Output is validated with veraPDF in CI.
8. **Printing** uses the display list: on desktop it is rendered to the operating system's print path as vector graphics (DESK-102); on the web, printing goes through generated PDF.

## Consequences

- One drawing model for screen, print and PDF means they cannot disagree about layout.
- We must build PDF/X ourselves; contributing upstream keeps maintenance shared.
- CPU rasterization must meet performance budgets on high-resolution displays; tiling and caching are mandatory.

## Alternatives considered

- **Platform 2D APIs (Direct2D, Core Graphics, Canvas 2D) for page content:** fast, but text and anti-aliasing differ per platform. Rejected for page content; acceptable for shell chrome.
- **Skia (C++):** excellent but violates ADR-0006 for glyph and image parsing paths and adds a heavy native build.
- **GPU-first (Vello on wgpu):** not bit-exact across GPUs; deferred.

## Validation gate

CORE-003: identical pixel hashes for the probe set on Linux x86-64, Windows x86-64, macOS arm64 and wasm32 in reference mode; rasterization throughput for a 1920×1080 viewport at 2× scale; a recommendation on vello_cpu for interactive use.

## Revisit when

Reference rasterization misses performance budgets after optimization, or tiny-skia loses maintenance (then evaluate vello_cpu with a bit-exact mode, contributing it upstream if needed).
