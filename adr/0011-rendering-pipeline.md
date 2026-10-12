# ADR-0011: Rendering pipeline — display lists, reference rasterizer, PDF

- **Status:** Accepted — validated by CORE-003 (2026-10-12); vello_cpu not adopted for interactive rendering
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

## Validation result (CORE-003, 2026-10-12)

The gate is met: the reference mode is bit-exact and fast enough, and Decision 2 stands as written. The recommendation on vello_cpu is not to adopt it for on-screen rendering (Decision 3). The [CORE-003 report](https://github.com/BayanDocs/bayan-core/pull/18) (`spikes/text-pipeline/REPORT.md` in bayan-core) has the evidence.

- **Reference mode (Decision 2).** tiny-skia 0.12.0 drew the gate's 30 probes and a full 3840 × 2160 screen of text with identical pixels (the SHA-256 of the RGBA8 image) in eleven environments: natively on Linux x86-64, Windows x86-64 and macOS arm64, and in WebAssembly, built with and without simd128, in Node.js on the three systems and in headless Chromium (the pull request's first CI run, on 2026-10-12). It is built with `default-features = false, features = ["no-std-float"]`. Without its `simd` feature every target runs tiny-skia's portable code, the single portable path this decision foresees: its SIMD paths use approximate reciprocals and min and max instructions whose NaN and signed-zero results differ between processors. With `no-std-float` its path geometry takes `acos`, `cos` and `powf` from the pure-Rust libm instead of each platform's math library (ADR-0005 §4). Relaxed SIMD is never enabled. The portable code still calls Rust's `f32::min` and `f32::max`, which leave the sign of a zero result unspecified, in its clipper; there the values are only compared or turned into fixed point, where both zeros are the same, so this cannot change a pixel, and `bayan-raster` replaces them with explicit comparisons. Nothing had to be patched.
- **Throughput:** the full 1920 × 1080 viewport at device scale 2, drawn untiled on one core, takes 39 to 56 ms natively and 144 to 290 ms in WebAssembly; the simd128 build, with the same pixels, is 21 to 36 % faster than the build without SIMD.
- **Interactive rasterizer (Decision 3): vello_cpu is not adopted.** vello_cpu 0.3.0 differs from the reference by up to 79 of 255 levels per channel, on 3.5 to 12.4 % of the pixels. The differences are anti-aliasing, not geometry (about as many pixels lighter as darker, all at or next to edges): tiny-skia samples each pixel at 4 × 4 positions, while vello_cpu computes the exact area covered, so no rasterizer that anti-aliases differently from the reference can meet ±2. It is 1.7 to 2.9 times as fast as the reference natively, but only 1.1 to 1.5 times in WebAssembly, where the web app runs the engine, and at the SIMD level it detects, its output depends on whether the processor fuses multiply-adds. On-screen rendering therefore uses the reference rasterizer, with tiling and caching. If an interactive rasterizer is wanted later, this decision's tolerance should first be restated in terms that a different anti-aliasing method can meet. Forced to its portable level, vello_cpu was also bit-identical in all eleven environments, which makes it the concrete candidate under "Revisit when" if tiny-skia loses maintenance.
- **Glyphs, gamma and blending (Decision 4), as CORE-003 fixed them:** skrifa outlines, unhinted, at the font's default instance; each point converted to device pixels with exact IEEE-754 operations in `f64` and rounded once to `f32`, glyph origins not snapped to pixels; coverage from tiny-skia's 4 × 4 supersampling, grayscale, non-zero fill; opaque black text on an opaque white page, composited source-over directly on the stored sRGB values (no gamma correction); 8-bit premultiplied RGBA without colour management. Gamma-2 blending, the alternative, is deterministic too, but changes every edge pixel by up to 64 levels and costs 3 to 55 % more time; it is not used for the reference. Gamma or contrast adjustments for the look of text would belong to the screen path only, and would need an amendment saying so, because the screen would then differ from the reference.

## Revisit when

Reference rasterization misses performance budgets after optimization, or tiny-skia loses maintenance (then evaluate vello_cpu with a bit-exact mode, contributing it upstream if needed).
