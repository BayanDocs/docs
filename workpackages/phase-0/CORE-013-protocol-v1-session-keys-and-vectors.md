# CORE-013: Engine protocol v1, part 1 — the session, keys, revisions, accessibility limits and the conformance vectors

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | UI / engine |
| Repository | bayan-core, and a small docs pull request that marks the items implemented |
| Attach to session | bayan-core, docs; bayan-desktop and bayan-web read-only, to see how the shells use the boundary today |
| Size | L |
| Depends on | CORE-007, CORE-010 |
| Unblocks | CORE-014, DESK-004, WEB-004 |
| Status | Kept in the [work package index](../README.md) |
| Requirements | ARC-03, ARC-07, A11Y-02, A11Y-03, SEC-01, SEC-10, UI-01 |
| Decisions | ADR-0002, ADR-0006, ADR-0012, ADR-0014 (amendment of 2026-10-12), ADR-0019, ADR-0020, ADR-0021 |
| Specs | [engine-protocol.md §14 and §15](../../specs/engine-protocol.md#14-protocol-v1-the-agreed-changes) |

## Context

Engine protocol v0 left behavior to the shells, and the shells decided it differently: which keys reach the engine, how often a failed engine is restarted, what happens to accessibility trees beyond their limits, after a refused `hello`, to the version `v` of incoming messages and to the tile grid's rounding (architecture reviews [H5](../../plan/reviews/2026-10-27.md#h5-the-engine-protocol-leaves-behavior-to-the-shells-and-they-already-decide-differently) and [H8](../../plan/reviews/2026-11-20.md#h8-the-shells-keep-diverging-while-the-protocol-work-of-h5-waits)). The planning session PLAN-PROTO decided protocol v1 contract-first in [spec §14](../../specs/engine-protocol.md#14-protocol-v1-the-agreed-changes) and specified shared test cases, the conformance vectors, in [§15](../../specs/engine-protocol.md#15-conformance-vectors). This work package builds the engine's side of every change of v1 that is not additive, so that the engine speaks v1 and both shells can move to it (DESK-004, WEB-004), and writes the vectors' first set. [CORE-014](CORE-014-protocol-v1-text-input-clipboard-and-a11y.md) then adds the rest of v1, additively.

Where things are today, at bayan-core `3423a4f`: the protocol's Rust types and `PROTOCOL_VERSION` in `crates/bayan-engine/src/protocol.rs`; the envelope's version check in `envelope.rs`; the handshake and the events in `engine.rs`; the stub manifest in `manifest.rs`; panic recovery in `engine.rs` and `thread.rs` (native) and in `restart()` of `crates/bayan-wasm/js/bayan-worker.js` (web); the C interface in `crates/bayan-ffi` with its generated header; the committed schema and TypeScript declarations in `crates/bayan-engine/protocol/`; and their packaging into the C SDK and the WebAssembly package in `xtask/src/artifacts.rs`.

## Objective

The engine, its C interface and its worker host implement spec §14.1, §14.2, §14.3, §14.6, item 1 of §14.7 and §14.8 as protocol version 1, and bayan-core ships the conformance vectors of §15, with their first set, in the C SDK and the WebAssembly package.

## Scope

### In scope

- **Versions and the handshake (§14.1):** `PROTOCOL_VERSION` 1; a `hello` read whatever its `v`; the refusal's `args.supported`; `hello.shell.platform` from the fixed list and the new `hello.shell.runtime`, an unknown or missing value counting as `other` and `native`; `engine_version` in `welcome` and in the worker host's `ready` at most 64 ASCII characters of Semantic Versioning, with a test.
- **Restarts (§14.2):** one implementation of the allowance in `bayan-engine`, a pure function of the times the bindings pass (no clock in the engine), used by the native engine thread with `bayan-ffi`'s times and by the worker host through `bayan-wasm`, which keeps the times of earlier restarts when it replaces the instance; a restart counting while it is less than 600,000 ms old; `restart` on every `engine.error` with `recoverable: false`, added by the binding after the engine has digested its messages; the stopped state (natively `BAYAN_STATUS_INTERNAL_ERROR` from `bayan_engine_post` and `bayan_render_tile`; on the web every message ignored, as after `failed`). Recordings and replays as item 4 of §14.2 says: the allowance's history outside `initial_state`, no counting inside a replay session on desktop, counting on the web where such a panic replaces the instance, and a desktop recording that spans a restart replaying with every digest equal.
- **Keys (§14.3):** the v1 stub manifest: each command's `bindings`, resolved for the session's platform and runtime with labels as the platform writes them, in the JSON shapes that §14.3 gives for bindings, document keys and reserved keys; the commands `edit.copy`, `edit.cut` and `edit.paste` with their `shell_action`; `keys.document`; `keys.reserved` as the spec's table gives it for each platform and runtime; v0's `shortcut` removed. The engine decides what an `input.key` means from the same bindings by the spec's matching rule (ASCII letters without regard to case, every other character exactly, the fallback to `code`). The mock document still acts only on the keys it handles today.
- **Revisions and invalidation (§14.6):** a render revision per document, below 2⁵³, in `doc.opened`, `render.invalidate`, `overlay.update` and the reply to `render.tile`; the new last parameter `uint64_t *revision_out` of `bayan_render_tile` (the header regenerated by cbindgen, the spec's §3.1 declarations updated in the docs pull request); a `view.set` that invalidates as item 2 says: nothing for a new viewport, zoom or device scale in a mode whose layout does not follow the window, what the new layout changes in `web` (the mock document lays `web` out like `print` today, which the tests record), and every page for a new `mode` or `show_formatting_marks`.
- **Accessibility limits (§14.7 item 1):** the depth limit with flattening; children given in unbroken runs with `child_count` and `children_start`, filled breadth-first in reading order with the path to the caret always included; `query.a11y { node, children: { start, count } }`, which answers at least one child whenever the node has one at `start`; tests with synthetic trees, because the mock document's tree is small, including a node with more children than one message holds.
- **The module's integrity (§14.8):** `wasm_integrity` in the worker host's `init`, passed to the module's fetch; a mismatch reported as `failed` with `load_failed`.
- **Conformance vectors (§15):** the folder `crates/bayan-engine/protocol/conformance/`, the files' format and a JSON Schema for them, both artifacts shipping them, and the first set: `restart.json`, `tile-grid.json`, `a11y-limits.json` and `keys.json`. bayan-core's tests check every `engine` and `binding` case against the code, and every expected result of a `shell` case against a reference implementation in the tests that is independent of the code under test (for example the tile-grid formula of §14.6 written out in a test).
- The schema and TypeScript declarations regenerated; the fuzz targets' seeds and dictionaries extended with the new fields; `bayan-engine`'s documentation; and a docs pull request that marks this work package's items implemented in the spec's status line and updates §3.1's declarations.

### Out of scope

- Replacing text, `input.select`, `query.hit`, the clipboard messages and the accessibility tree's content (CORE-014).
- Any change in bayan-desktop or bayan-web (DESK-004, WEB-004), including the stub engine of bayan-desktop.
- Real documents, real layout and the real accessibility tree (CORE-125, CORE-128), and the questions of [§14.9](../../specs/engine-protocol.md#149-still-open).

## Deliverables

- The changes above in `bayan-engine`, `bayan-ffi`, `bayan-wasm` and its worker host, with tests.
- `crates/bayan-engine/protocol/conformance/` with the four files and their schema, shipped as `schema/conformance/` in the C SDK and `conformance/` in the WebAssembly package.
- The regenerated `engine-protocol.schema.json`, `engine-protocol.d.ts` and `bayan_ffi.h`.
- The docs pull request described above.

## Acceptance criteria

- [ ] AC-1 The engine speaks only v1: a `hello` with any `v` that offers 1 is welcomed with `v: 1`; one that does not is refused with `unsupported_protocol_version` listing `[1]`; every other message with a `v` other than 1 is refused; tests cover each case, and `PROTOCOL_VERSION` becomes 1 in the pull request that completes the non-additive changes (§9).
- [ ] AC-2 Platform and runtime are parsed as §14.1 says, unknown values counting as `other` and `native`, and a test shows that nothing but the manifest's key data depends on them.
- [ ] AC-3 Both bindings apply the restart allowance of §14.2 through one implementation: tests with controlled times show `restart` numbered 1 to 3 within ten minutes, `null` on the fourth failure, the allowance refilling as earlier restarts leave the window (a restart 599,999 ms old still counts, one 600,000 ms old does not), and the stopped state of each binding; a desktop recording that spans a restart replays with every digest equal, and a panic inside a replay does not count on desktop; every case of `restart.json` marked `binding` passes against both bindings.
- [ ] AC-4 The stub manifest's bindings, document keys, reserved keys and shell actions match `keys.json` for every platform and runtime, and the engine runs a binding's command for exactly the presses that `keys.json` says a shell sends.
- [ ] AC-5 Render revisions as §14.6 item 1 says, on both tile paths, with a test in which an invalidation and a tile that crossed in time carry revisions that tell the shell what is current; `view.set` invalidates as item 2 says, mode by mode.
- [ ] AC-6 Accessibility trees beyond the limits are flattened and split as §14.7 item 1 says: a node with more children than one message holds is loaded completely through `children` ranges, each answer within the message limits, and the part that holds the caret comes with the first answer; every `engine` case of `a11y-limits.json` passes.
- [ ] AC-7 `wasm_integrity` works: the worker host's browser tests start the engine with the right hash and fail to with a wrong one (`failed`, `load_failed`).
- [ ] AC-8 Both artifacts ship the vectors and their schema next to the protocol's schema; every expected result of a `shell` case is checked by a reference implementation in bayan-core's tests; `engine_version` meets its limit.
- [ ] AC-9 `cargo xtask verify` passes; no dependency is added (or each is justified as AGENTS.md §5 asks); the docs pull request is open and linked.

## Verification

`cargo xtask verify` (bayan-core's gate), which also builds both artifacts and runs the worker host's browser tests; `cargo xtask wasm-package` and the C SDK command list the conformance files in the packages; the docs pull request passes `scripts/verify.sh`.

## Notes and pitfalls

- The work package may take up to three pull requests. Only the last switches `PROTOCOL_VERSION` to 1, so that no core commit speaks a v1 that later changes shape; the shells' work packages pin the commit that completes this one.
- The engine reads no clock and no environment (ADR-0012 decision 5, the outside-world check of `cargo xtask verify`): the allowance takes times as arguments. The native times come from `bayan-ffi`, which already passes them with each message and tile for recordings; a panic outside a message uses the time of the job that was running.
- On the web, `__wbg_reset_state()` discards everything in the WebAssembly instance, so the times of earlier restarts live in the worker host's JavaScript and are handed to the new instance, or to a pure function of the new module, never kept in the old one.
- The key-matching rule deliberately needs no Unicode script data (§14.3); do not add a dependency for it.
- `bayan-desktop` keeps byte-for-byte copies of the header and schema, and its stub engine implements the header; this work package changes neither repository, but its hand-off notes tell DESK-004 what changed in the header.
- Treat the vectors as part of the contract: a case changes only with the spec, in the same pull request as the code it tests (§15).

## Escalate if

- Any part of §14 cannot be built as written, or would need a further change of the protocol or of an Accepted ADR.
- Keeping the outside-world check green would need an exemption for the restart allowance.
- A new dependency seems necessary.
