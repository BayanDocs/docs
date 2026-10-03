# ADR-0005: Integer layout units (BLU) and deterministic math

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** FID-02, ADR-0004, CORE-002, CORE-003

## Context

Layout must produce identical results on x86-64, arm64 and wasm32, and must be able to reproduce Word's own rounding. OOXML mixes many units: twips (1/1440 inch), EMUs (1/914,400 inch), points, half-points, eighths of a point, fiftieths of a percent, sixty-thousandths of a degree. Basic IEEE-754 operations are deterministic in Rust on all our targets, but transcendental functions (`sin`, `exp`, `powf`) come from platform math libraries and differ between platforms; floating-point accumulation also makes "where does Word round?" questions hard to reason about.

## Decision

1. **All layout geometry uses the Bayan Layout Unit (BLU)**, stored as `i64`: **1 BLU = 1/1,828,800 inch = 1/25,400 point.** Every common unit is an exact integer number of BLU:

   | Unit | BLU | Unit | BLU |
   |---|---|---|---|
   | inch | 1,828,800 | point | 25,400 |
   | twip (1/20 pt) | 1,270 | half-point | 12,700 |
   | EMU | 2 | eighth of a point | 3,175 |
   | millimetre | 72,000 | centimetre | 720,000 |
   | pixel at 96 dpi | 19,050 | pixel at 72 dpi | 25,400 |
   | dot at 300 / 600 / 1200 dpi | 6,096 / 3,048 / 1,524 | dot at 144 dpi | 12,700 |

   This lets us represent exactly any value Word computes in twips, points, EMUs or common device resolutions, so the Word measurement model (ADR-0009) can round precisely where Word rounds.
2. **Scaling from font units** (for example advance widths in a 2048-unit em at 11 pt) uses exact rational arithmetic in integers with an explicit, documented rounding mode at each step. The rounding points are determined by the Fidelity Lab, not guessed.
3. **No floating point in layout.** `bayan-layout`, `bayan-text` measurement, `bayan-styles` and `bayan-fields` numeric code use BLU and integer or fixed-point types only.
4. **Floating point is allowed in rendering** (rasterization, color conversion) provided the code uses only IEEE-754 basic operations, avoids fused multiply-add unless explicit and identical on all targets, and takes transcendental functions from the pure-Rust `libm` crate or our own implementations in `bayan-units`. Platform `f32`/`f64` transcendental methods are forbidden by Clippy's `disallowed-methods` in all core crates.
5. **Determinism hygiene:** no iteration over hash maps with random state in anything that affects output (use `BTreeMap`, `IndexMap` with a fixed hasher, or sort); no wall-clock time, locale, environment or thread scheduling in output unless explicitly passed in by the host.
6. `bayan-units` provides the BLU type with checked arithmetic in debug builds, conversions, rounding helpers (floor, ceiling, half-up, half-even, half-away-from-zero, toward zero), geometry types (points, sizes, rectangles, insets, affine transforms in fixed point) and the deterministic math functions.

## Consequences

- Equality of layouts across platforms can be checked by hashing, and tests compare exact integers.
- Range is ample: `i64` BLU covers about five million kilometres.
- Developers cannot casually use `f32` in layout; the lint enforces it.

## Alternatives considered

- **`f64` everywhere with careful operations:** deterministic for basic operations, but rounding points become implicit and accumulation order matters; harder to match Word's rounding.
- **EMU as the base unit:** eighths of a point are not integral (1,587.5 EMU).
- **Twips as the base unit:** too coarse for glyph advances and Word's sub-twip computations.

## Revisit when

The lab proves Word computes some quantity in a unit that BLU cannot represent exactly (none known).
