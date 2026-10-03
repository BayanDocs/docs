# CORE-003: Spike — deterministic text pipeline across platforms

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | TEXT / OUTPUT |
| Repository | bayan-core |
| Attach to session | bayan-core, docs |
| Size | L |
| Depends on | CORE-002 |
| Unblocks | CORE-008, LAB-005, Phase-1 text and rendering work |
| Status | Ready |
| Requirements | FID-02, I18N-01, I18N-02, PERF-02, PERF-06 |
| Decisions | ADR-0004, ADR-0005, ADR-0009 and ADR-0011 (this spike is their validation gate) |
| Specs | [fidelity-lab.md §10](../../specs/fidelity-lab.md#10-determinism-suite) |

## Context

The whole Fidelity Contract rests on one claim: our own text stack produces bit-identical layout and pixels on Linux, Windows, macOS and in browsers. ADR-0009 chose harfrust, skrifa, ICU4X (dictionary segmentation) and unicode-bidi; ADR-0011 chose tiny-skia as the reference rasterizer and asked for vello_cpu to be evaluated for interactive rendering. This spike proves or disproves those choices before anything is built on them.

## Objective

Demonstrate identical layout hashes and identical reference-raster hashes for a multilingual probe set on five environments, and measure performance and WebAssembly size, with a written recommendation.

## Scope

### In scope

- A spike crate under `spikes/text-pipeline/` (or an early `bayan-text` prototype if clean enough) that:
  - loads open fonts from files fetched by a script with pinned SHA-256 checksums (Liberation Sans/Serif, Carlito, Noto Naskh Arabic, Noto Sans Hebrew, Noto Sans Devanagari, Noto Sans Thai, and a Noto CJK subset); fonts are not committed unless small;
  - itemizes text by script and bidi level (unicode-bidi with ICU4X data), segments with ICU4X (dictionary models for Thai), shapes with harfrust (with kerning on and off), measures in BLU via `bayan-units`;
  - breaks lines greedily at a fixed width using UAX #14 opportunities (no Word tailoring yet) and reorders bidi lines;
  - writes a layout JSON (glyph IDs, positions in BLU, line boxes) and its SHA-256;
  - rasterizes the lines from skrifa outlines with tiny-skia in a reference mode (relaxed SIMD disabled), writes PNG and its hash; does the same with vello_cpu for comparison.
- A probe set of about 30 paragraphs: Latin with kerning on/off and ligatures, Arabic with marks, Hebrew mixed with numbers and Latin, Devanagari, Thai, Chinese, Japanese, a colour emoji (optional).
- A CI matrix job producing hashes on Linux x86-64, Windows x86-64, macOS arm64, wasm32 under Node, and wasm32 in headless Chromium, plus a job that compares them and fails on any difference.
- Measurements: shaping throughput (characters per second), rasterization time for a 1920×1080 viewport at device scale 2, WebAssembly size added (gzip and brotli), memory.
- Fix nondeterminism found (for example by forcing a single code path) and document every fix.
- A report in `spikes/text-pipeline/REPORT.md` and a summary pull request to docs updating the validation status of ADR-0009 and ADR-0011 (and proposing amendments if needed).

### Out of scope

Word-compatible line breaking, the Word measurement model (LAB-005), production APIs.

## Deliverables

Spike code, CI jobs, report, docs pull request.

## Acceptance criteria

- [ ] AC-1 Layout JSON hashes are identical across all five environments for every probe.
- [ ] AC-2 Reference-mode raster hashes are identical across all five environments, or the report identifies the root cause with a concrete, tested fix plan.
- [ ] AC-3 The report gives throughput, raster timing, size and memory figures, and a recommendation on vello_cpu for interactive rendering (with its measured pixel tolerance versus the reference).
- [ ] AC-4 The report documents gamma and blending choices for glyph rendering.
- [ ] AC-5 All dependencies are pinned, at least 24 hours old, allowlisted and justified.

## Verification

CI matrix and comparison job links; `cargo xtask verify`.

## Notes and pitfalls

- WebAssembly relaxed-SIMD results are implementation-defined; keep it disabled.
- Fused multiply-add can creep in through SIMD intrinsics; check tiny-skia's code paths per target.
- ICU4X's LSTM segmenter models must not be used (floating point).

## Escalate if

Bit-exact rasterization cannot be achieved with either rasterizer without unacceptable performance loss; the planner will decide whether Tier A pixel identity becomes geometry identity only.
