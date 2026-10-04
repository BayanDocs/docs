# CORE-001: Core workspace scaffold and verification gate

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | MODEL / RELEASE |
| Repository | bayan-core |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | — |
| Unblocks | CORE-002…CORE-008, LAB-001, LAB-003, X-003 |
| Status | Ready |
| Requirements | ARC-01, ARC-02, SEC-01, FID-02 |
| Decisions | ADR-0005, ADR-0006, ADR-0017, ADR-0025 |
| Specs | [plan/03-architecture.md §4](../../plan/03-architecture.md#4-inside-bayan-core) |

## Context

bayan-core is empty. Every later core work package builds on the workspace layout, lint configuration and verification gate created here, so the conventions set now matter for years. Read ADR-0005 (no floating point in layout, deterministic math), ADR-0006 (no `unsafe` outside binding crates, toolchain pinning) and ADR-0017 (exact pins, minimum age) before starting.

## Objective

A Cargo workspace with the crate skeletons needed in Phase 0, strict lints that enforce determinism and safety rules, and a single command, `cargo xtask verify`, that CI runs on Linux, Windows and macOS and for wasm32.

## Scope

### In scope

- `Cargo.toml` workspace: edition 2024, resolver 3, `[workspace.package]` (repository URL, `rust-version` matching the toolchain, `license = "GPL-3.0-or-later WITH AdditionRef-BayanDocs-App-Store-Permission"` per ADR-0003 §4, the SPDX 3.0 form that cargo-deny accepts), `[workspace.dependencies]` with exact `=x.y.z` requirements, `[workspace.lints]` with `unsafe_code = "forbid"` (overridden only in `bayan-ffi` and `bayan-wasm`), and a curated Clippy set (all warnings denied in CI, a pedantic subset).
- `rust-toolchain.toml`: the latest stable Rust release that is at least 24 hours old (record its version and release date in the pull request), components `rustfmt` and `clippy`, target `wasm32-unknown-unknown`.
- `clippy.toml`: `disallowed-methods` for floating-point transcendental and platform math methods on `f32`/`f64` (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `exp`, `exp2`, `exp_m1`, `ln`, `log`, `log2`, `log10`, `ln_1p`, `powf`, `powi`, `cbrt`, `hypot`), with a message pointing to `bayan-units`; `disallowed-types` for `std::collections::HashMap` and `HashSet` (allowed only via `#[expect]` with a justification where iteration order cannot affect output).
- Crate skeletons with crate-level documentation stating their responsibility and layer: `bayan-units`, `bayan-opc`, `bayan-xml`, `bayan-crdt`, `bayan-model`, `bayan-engine`, `bayan-ffi`, `bayan-wasm`, `bayan-cli`. Layout: `crates/<name>/`, `xtask/`, `lab/` (empty README), `fuzz/` (empty README), `spikes/` (README explaining that spikes are excluded from release builds).
- `xtask` with `cargo xtask verify` running, in order: `cargo fmt --check`, `cargo clippy --workspace --all-targets --all-features -- -D warnings`, `cargo test --workspace --locked`, a wasm32 build of every crate that must support WebAssembly, `cargo doc --workspace --no-deps` with warnings denied, and `cargo deny check` (tool installed in CI at a pinned version with checksum verification). Leave clearly named hooks for the X-003 checks and for future determinism checks.
- CI workflow running `cargo xtask verify` on `ubuntu-24.04`, `windows-latest` and `macos-latest` (arm64), following the workflow conventions of ADR-0017 (SHA-pinned actions, minimal permissions, timeouts). Caching only with first-party actions.
- `.cargo/config.toml` with `[registry] global-min-publish-age = "1 day"` (inactive until Rust 1.100, see ADR-0017).
- Update this repository's `AGENTS.md` with the real commands.

### Out of scope

- Any functionality inside the crates (later WPs).
- License files: `LICENSE`, `LICENSES/` and `REUSE.toml` already exist; keep `reuse lint` passing (the REUSE CI job comes with X-001).
- Supply-chain scripts (X-003).

## Deliverables

Workspace, crate skeletons, `xtask`, configuration files, CI workflow, updated `AGENTS.md`.

## Acceptance criteria

- [ ] AC-1 `cargo xtask verify` passes locally and in CI on all three operating systems; the wasm32 build passes.
- [ ] AC-2 A test or documented demonstration shows that calling `f64::sin` in a core crate fails the lint, and that `unsafe` in a non-binding crate fails to compile.
- [ ] AC-3 All dependencies (including `xtask` dependencies) are exact-pinned, at least 24 hours old, on the ADR-0017 license allowlist, and justified in the pull request; the transitive count is reported.
- [ ] AC-4 Each crate's documentation states its layer and the layering rule from the architecture document.
- [ ] AC-5 CI completes in under 15 minutes.

## Verification

`cargo xtask verify`; CI links for the three platforms.

## Notes and pitfalls

- Keep `xtask` dependencies minimal (prefer the standard library and `std::process::Command`).
- `cargo-deny` needs a `deny.toml`; add a minimal one (X-003 completes it).

## Escalate if

The latest stable toolchain is younger than 24 hours and the previous one lacks something you need; or a lint rule required by ADR-0005 cannot be expressed in Clippy.
