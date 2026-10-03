# CORE-002: `bayan-units` — integer layout units and deterministic math

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | TEXT / LAYOUT |
| Repository | bayan-core |
| Attach to session | bayan-core, docs |
| Size | S |
| Depends on | CORE-001 |
| Unblocks | CORE-003, CORE-004, all layout work |
| Status | Ready |
| Requirements | FID-02 |
| Decisions | ADR-0005 (implement it exactly) |
| Specs | — |

## Context

ADR-0005 defines the Bayan Layout Unit (BLU = 1/1,828,800 inch = 1/25,400 point) as the integer unit of all layout arithmetic, and requires deterministic math for anything else. This crate is the foundation every other core crate uses for geometry.

## Objective

A small, exhaustively tested crate providing BLU, exact unit conversions, explicit rounding, geometry types and deterministic math.

## Scope

### In scope

- `Blu(i64)` with arithmetic operators (checked in debug builds, with explicit `checked_*`/`saturating_*` variants), ordering, hashing, `Display` and `serde` support.
- Exact constants and constructors/accessors for every unit in ADR-0005's table (inch, point, twip, half-point, eighth of a point, EMU, millimetre, centimetre, pixels at common DPIs).
- Parsing of OOXML measurements: integer twips, EMUs, half-points, eighths of a point, fiftieths of a percent and thousandths, sixty-thousandths of a degree, and Strict OOXML universal measures with units (`"12pt"`, `"1.5in"`, `"2cm"`, `"10mm"`, `"3pc"`, `"4pi"`), rejecting anything malformed.
- Rational scaling helper: `scale(value, numerator, denominator, Rounding)` computed in 128-bit integers, with a `Rounding` enum (floor, ceiling, half-up, half-even, half-away-from-zero, toward zero). This is what the font-unit-to-BLU conversion will use.
- Geometry: `Point`, `Size`, `Rect`, `Insets`, and a fixed-point affine `Transform` suitable for rotations and scaling of drawing objects.
- Deterministic math: sine and cosine for transforms (fixed-point or via the pure-Rust `libm` crate), with tests showing identical results on all targets.
- Property-based tests (`proptest`): conversion round trips are exact; rounding modes match a big-integer reference implementation; arithmetic does not overflow for any realistic document dimension.

### Out of scope

Any text or layout logic.

## Deliverables

The crate with documentation and examples; tests.

## Acceptance criteria

- [ ] AC-1 Every conversion in ADR-0005's table is exact and covered by a test.
- [ ] AC-2 Property-based tests pass, including on wasm32 (via `wasm-bindgen-test` or Node).
- [ ] AC-3 The public API exposes no floating-point types except an explicitly named lossy conversion for display and debugging.
- [ ] AC-4 Deterministic math functions return identical bit patterns on Linux x86-64, Windows x86-64, macOS arm64 and wasm32 for a fixed test vector (CI evidence).
- [ ] AC-5 `cargo xtask verify` passes.

## Verification

`cargo xtask verify`; CI matrix results for AC-4.

## Escalate if

A conversion required by OOXML cannot be represented exactly in BLU (contradicting ADR-0005).
