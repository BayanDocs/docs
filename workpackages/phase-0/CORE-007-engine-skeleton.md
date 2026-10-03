# CORE-007: Engine skeleton — protocol v0, C ABI and WebAssembly worker host

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | UI / engine |
| Repository | bayan-core |
| Attach to session | bayan-core, docs |
| Size | L |
| Depends on | CORE-001 (uses CORE-003's pipeline for text if merged; otherwise draws vector placeholders) |
| Unblocks | DESK-002, WEB-002, SRV-003, CORE-125 |
| Status | Ready |
| Requirements | ARC-02, ARC-07, ARC-08 |
| Decisions | ADR-0012 (implement it), ADR-0006 (`unsafe` only in binding crates), ADR-0002 (artifacts) |
| Specs | [engine-protocol.md](../../specs/engine-protocol.md) |

## Context

The desktop and web shells need a real engine to integrate against long before the engine can open documents. This work package builds the engine's outer shell: the message protocol, threading, bindings and artifacts, around a **mock document** (a fixed multi-page test document), so DESK-002 and WEB-002 can prove scrolling, tiles, input and accessibility end to end.

## Objective

A working `bayan-engine` with protocol v0, a C ABI for desktop, a WebAssembly build with a worker host for the web, record and replay, and CI artifacts that the shells can consume.

## Scope

### In scope

- **`bayan-engine`:** an actor that processes messages in order on its own thread (native) or in the worker (WebAssembly); message envelope, handshake and the v0 messages needed by the spikes: `hello`/`welcome`, `doc.open` (opens the mock document regardless of input), `view.set`, `view.pages`, `render.invalidate`, `render.tile`, `overlay.update`, `input.pointer`, `input.key`, `input.text`, `input.composition` (the mock document has one editable line that shows received text and composition so the IME path is visible), `query.a11y` and `a11y.update` (a mock accessibility tree with a heading, paragraphs, a list and a small table), `ui.manifest` (a tiny stub), `diag.record.start/stop`, `engine.error`.
- **Mock rendering:** pages with text through CORE-003's pipeline if available; otherwise vector shapes and placeholder bars. Tiles in premultiplied RGBA8.
- **Types and schema:** message types in Rust with `serde`; JSON Schema generated (`schemars` or equivalent) and TypeScript declarations generated, both emitted as build artifacts.
- **`bayan-ffi`:** the C ABI from spec §3 with a cbindgen-generated header committed to the repository; every entry point catches panics and converts them to `engine.error`; `// SAFETY:` comments; Miri tests for pointer-handling helpers where feasible.
- **`bayan-wasm`:** wasm-bindgen build plus a dependency-free worker host script (`bayan-worker.js`) relaying messages and producing `ImageBitmap` tiles; a minimal HTML page for manual testing.
- **Record and replay:** recordings captured via `diag.record.*`; a test that replays a recording and checks identical tile hashes.
- **Test drivers:** a small **C** program (not C++) that links the static library and runs handshake → open → render a tile → record → replay; a Node test doing the same through the WebAssembly build.
- **Artifacts in CI:** C SDK per target (Linux x86-64, Windows x86-64, macOS arm64; static and dynamic libraries, header, JSON Schema) and the WebAssembly package (`.wasm`, JavaScript glue, TypeScript declarations), uploaded as workflow artifacts with checksums. No releases yet.

### Out of scope

Real document opening, editing, the real UI manifest.

## Deliverables

Engine, bindings, worker host, schema and type generation, test drivers, CI artifacts, updated spec if anything had to change (docs pull request).

## Acceptance criteria

- [ ] AC-1 The C driver and the Node driver both complete the handshake → open → render → record → replay flow in CI on every target.
- [ ] AC-2 Replay reproduces identical tile hashes.
- [ ] AC-3 A forced panic inside a message handler produces `engine.error` and the engine stays usable or restarts cleanly (test).
- [ ] AC-4 JSON Schema and TypeScript declarations are generated in CI and match the Rust types (a test validates sample messages against the schema).
- [ ] AC-5 `unsafe` appears only in `bayan-ffi` and `bayan-wasm`, each block documented.
- [ ] AC-6 Artifacts for all targets are produced with checksums.

## Verification

`cargo xtask verify`; CI artifact links; driver outputs.

## Notes and pitfalls

- Callbacks run on the engine thread; document that shells must not call back into the engine synchronously.
- Keep the worker host free of npm dependencies.

## Escalate if

A protocol change is needed; propose it to `specs/engine-protocol.md` in a docs pull request first.
