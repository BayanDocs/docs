# ADR-0006: Rust core and memory-safety policy for untrusted input

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** ARC-01, ARC-02, SEC-01, ADR-0017, CORE-001

## Context

The engine parses hostile input all day: ZIP packages, XML, fonts, images, metafiles, field codes, network messages. Historically, most critical vulnerabilities in office suites came from memory-unsafe parsers. The engine must also compile to native code on three operating systems and to WebAssembly. The owner chose Rust for the core.

## Decision

1. **The core is Rust** (edition 2024), with the toolchain pinned in `rust-toolchain.toml` to an exact stable release and updated only in batched dependency sessions. Rust 1.100 (2026-11-12) is the first stable release with Cargo's native minimum-publish-age setting (ADR-0017); the workspace adopts it in the first update session after it is at least 24 hours old.
2. **`#![forbid(unsafe_code)]`** in every crate except the binding crates (`bayan-ffi`, `bayan-wasm`). Any other crate needing `unsafe` (for example a SIMD fast path) requires an ADR amendment naming the crate and the justification, and every `unsafe` block carries a `// SAFETY:` comment and Miri coverage.
3. **No C or C++ libraries parse untrusted input** in the core, shells or server when a maintained memory-safe alternative exists. Where no alternative exists, the native code runs out of process or inside a WebAssembly sandbox, and the exception is recorded in an ADR (the only planned exception is local AI inference, ADR-0024). Native libraries that only process data the program itself generates are outside this rule but must be justified in the work package that introduces them; the planned case is SQLite in the server, which stores server-generated metadata through bound parameters and never parses documents or client-supplied SQL. Likewise, the desktop shell must not use Qt to decode document content, embedded images, fonts from documents or clipboard payloads; it passes raw bytes to the engine.
4. **Panics never cross a language boundary.** Every FFI and WebAssembly entry point catches panics and turns them into error events; the engine then discards the affected session state and offers recovery from the auto-recovery journal. Library crates use `panic = "unwind"`; the WebAssembly build reports panics to the worker host, which restarts the engine.
5. **Resource limits everywhere:** every parser and layout pass enforces limits on size, depth, count and time, and is cancellable.
6. **Lints:** `clippy` with warnings as errors, a curated pedantic subset, and `disallowed-methods`/`disallowed-types` for nondeterministic APIs (ADR-0005).
7. **The toolchain is the minimum supported Rust version.** BayanDocs is an application, not a library ecosystem, so there is no separate MSRV policy.

## Consequences

- Entire classes of vulnerabilities (buffer overflows, use-after-free) are eliminated from parsing.
- Some mature C libraries (HarfBuzz, FreeType, LittleCMS, libxml2) are not used directly; their Rust ports or equivalents are (ADR-0009, ADR-0011).
- Contributors need Rust skills; the owner follows the learning path.

## Alternatives considered

- **C++ core shared with the Qt shell:** one less language, but memory-unsafe parsing of hostile input. Rejected.
- **Go or another garbage-collected language:** poor WebAssembly size and performance for this workload.
- **Allowing well-known C libraries behind safe wrappers:** wrappers do not remove the bugs inside. Rejected for parsing.

## Revisit when

A required capability has no viable memory-safe implementation and cannot be isolated.
