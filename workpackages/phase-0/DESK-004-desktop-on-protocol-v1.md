# DESK-004: The desktop on engine protocol v1 — sessions, restarts through core, keys, revisions and accessibility limits

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | DESKTOP / UI |
| Repository | bayan-desktop |
| Attach to session | bayan-desktop, bayan-core (read, for the SDK, its header, schema and conformance vectors), docs |
| Size | L |
| Depends on | CORE-013, DESK-003 |
| Unblocks | DESK-005 |
| Status | Kept in the [work package index](../README.md) |
| Requirements | ARC-03, ARC-07, A11Y-02, A11Y-03, UI-01 |
| Decisions | ADR-0002, ADR-0006, ADR-0012, ADR-0013, ADR-0019, ADR-0020 |
| Specs | [engine-protocol.md §14.1, §14.2, §14.3, §14.6, §14.7 and §15](../../specs/engine-protocol.md#14-protocol-v1-the-agreed-changes) |

## Context

[CORE-013](CORE-013-protocol-v1-session-keys-and-vectors.md) switches the engine to protocol v1 as [spec §14](../../specs/engine-protocol.md#14-protocol-v1-the-agreed-changes) decided it, and ships the conformance vectors of [§15](../../specs/engine-protocol.md#15-conformance-vectors). This work package moves bayan-desktop to it, and so removes the desktop's side of the differences that the architecture review of 2026-11-20 lists in [H8](../../plan/reviews/2026-11-20.md#h8-the-shells-keep-diverging-while-the-protocol-work-of-h5-waits). At `8e6fae4` the desktop sends every key but Tab, printable keys as both `input.key` and `input.text` (`src/canvas/documentcanvas.cpp`, `keyPressEvent`, and `src/canvas/keymapping.h`); counts its own restarts (`src/app/restartallowance.h`); refuses accessibility trees beyond 64 levels or 200,000 nodes and then exposes no text (`src/engine/protocol.h`, `src/app/documentsession.cpp`); stops for good after a refused `hello` without an update prompt; refuses any message whose `v` is not 0 (`src/engine/engine.cpp`); assumes that an invalidation belongs to the request answered last (`src/app/documentsession.cpp`, `src/canvas/tilecache.cpp`); and computes the tile grid with a tolerance of 10⁻⁶ (`src/canvas/tilegrid.cpp`). [WEB-004](WEB-004-web-on-protocol-v1.md) does the same for the web, and [DESK-005](DESK-005-desktop-text-input-clipboard-and-a11y.md) follows with CORE-014's additions.

## Objective

bayan-desktop speaks protocol v1 as §14.1, §14.2, §14.3, §14.6 and item 1 of §14.7 require, its stub engine does what the new header documents, and its unit tests pass every `shell` and `desktop` case of the conformance vectors of its pinned core.

## Scope

### In scope

- **The pin:** `deps/bayan-core.json` moves to the commit that completes CORE-013; the copies of the header and schema in `src/engine/stub/` follow, joined by byte-identical copies of the conformance vectors next to the schema, all compared with the SDK's by `engine.sdk_copies` whenever the app is built against one (§15). The stub implements v1 as far as the shell's tests use it: `revision_out`, the v1 manifest's key data, and its test switches. It does not count restarts: its `engine.error` carries the `restart` value that a test switch gives it, so that the rule is not written a third time.
- **Versions and the handshake (§14.1):** `hello` with `v: 1`, `platform` from the fixed list (from Qt's knowledge of the operating system, not its free-text product name) and `runtime: "native"`; `v` checked on every message but the reply to `hello`; a refused `hello` ends the engine's use, with the update prompt after `unsupported_protocol_version` (the installation is incomplete and must be updated or reinstalled; no update action yet, DESK-104); protocol violations as item 5 lists them, each field checked before use, ending the engine's use with §12.1's stop message; `engine_version` checked against its limit.
- **Restarts (§14.2):** `RestartAllowance` removed; the shell starts a new session when `engine.error` carries `restart`, tells the user "n of 3" from it, and stops on `restart: null`; §12.1's steps 2–4 unchanged.
- **Keys (§14.3):** the canvas sends `input.key` for exactly the presses that the manifest's bindings and document keys match and no reserved key matches, and lets every other press go on to Qt; it no longer sends `input.key` for typed text; `code` filled for letter and digit keys, and every other key whose position is known, from the platform's scan code; the manifest's labels shown where the interface shows shortcuts; `edit.copy`, `edit.cut` and `edit.paste` left to DESK-005, which wires them to the clipboard (until then their keys simply stay with Qt).
- **Revisions, invalidation and the tile grid (§14.6):** the new `bayan_render_tile` signature; the tile cache keeps a tile while no invalidation with a higher revision covers it, with no assumption about order; tiles for a new scale requested by the shell itself, since in a mode whose layout does not follow the window `view.set` no longer invalidates them, while in `web` mode the engine's invalidations after a new width or zoom say what to render again; `tilegrid.cpp` computing exactly the spec's formula, which it already does with the spec's tolerance.
- **Accessibility limits (§14.7 item 1):** trees beyond the limits treated as protocol violations; a node with `child_count` exposed with all its children, the parts it lacks loaded through `query.a11y { node, children: { start, count } }` when the accessibility bridge needs them (or earlier).
- **Conformance vectors (§15):** unit tests that read `restart.json`, `tile-grid.json`, `a11y-limits.json` and `keys.json` from the repository's copies (the pin bullet above), run every case marked `shell` or `desktop`, and fail on a case they do not recognize; they run in the shell's own gate against the stub, and the SDK jobs check that the copies equal the SDK's.
- Comments, `AGENTS.md`, `src/engine/README.md` and the docs repository's [bayan-desktop guide](../../developer/bayan-desktop.md), where they describe what changed (a linked docs pull request for the guide).

### Out of scope

- Replacing text, the caret, hit-testing, the clipboard and the accessibility tree's content (DESK-005).
- Zoom keys: the shell binds none; Ctrl+=, Ctrl+− and Ctrl+0 reach the engine only once a manifest binds them (§14.3).
- The manual tests of DESK-002's validation gate.

## Deliverables

- The changes above with their tests, and the stub engine on v1.
- Updated `AGENTS.md`, `src/engine/README.md` and a docs pull request for the developer guide.

## Acceptance criteria

- [ ] AC-1 The shell speaks v1: `hello` as §14.1 item 2 says, with a test per operating system's value; messages with another `v`, and each other kind of violation of item 5, end the engine's use with the stop message (tests through `tests/support/enginemessages.h`'s `deliverMalformed()`).
- [ ] AC-2 A refused `hello` ends the engine's use without a new `hello`; after `unsupported_protocol_version` the update prompt is shown and announced to screen readers, after any other error the stop message.
- [ ] AC-3 No restart counting is left in the shell or the stub; every `shell` case of `restart.json`, read from the repository's copy, passes in the gate against the stub (with `restart` values from its test switch), and the recovery tests pass against the real engine (`diag.panic` with `test.allow_panic`), including the stop after the fourth failure.
- [ ] AC-4 Every `shell` and `desktop` case of `keys.json` passes in a unit test of the key mapping, including the presses from Arabic, Russian, French and German layouts and with AltGr; typed text produces `input.text` only.
- [ ] AC-5 A tile and an invalidation that cross in time are resolved by their revisions (a test with the stub's or the engine's revisions), and zooming requests the new scale's tiles without an invalidation; every case of `tile-grid.json` passes.
- [ ] AC-6 Every `shell` case of `a11y-limits.json` passes; a node with more children than one message holds is exposed in full to Qt's accessibility interfaces after the shell has loaded its parts with `children` ranges.
- [ ] AC-7 `cmake --workflow --preset verify` passes, with the vector tests in it; CI's jobs against the real engine and under the sanitizers pass, and in them `engine.sdk_copies` finds the copies of the header, the schema and the vectors equal to the SDK's.

## Verification

`cmake --workflow --preset verify`; `scripts/build-engine-sdk.sh` and `scripts/test-engine-sdk.sh --sdk build/bayan-core-sdk --sanitizers`; CI on Linux, macOS and Windows.

## Notes and pitfalls

- Qt reports Command as Control on macOS by default; `keymapping.h` already swaps them back to the DOM's names, which the bindings use.
- Qt has no portable physical key code; the scan code differs per platform (Windows' set 1 scan codes, macOS's virtual key codes, Linux's evdev codes through XKB), so map each platform's codes for the keys whose position the DOM names, and test the maps.
- The callback of the C interface runs on the engine's thread; check messages after they reach the main thread, as today.
- Keep the stub faithful: tests that pass only against the stub prove nothing about the engine (DESK-003).

## Escalate if

- Any part of §14 cannot be built in Qt as written.
- Qt does not deliver a reserved key, or delivers one the table does not list, on one of the three platforms.
