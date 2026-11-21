# WEB-004: The web on engine protocol v1 — sessions, restarts through core, keys, revisions, accessibility limits and the module's integrity

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | WEB / UI |
| Repository | bayan-web |
| Attach to session | bayan-web, bayan-core (read, for the WebAssembly package, its schema and conformance vectors), docs |
| Size | L |
| Depends on | CORE-013, WEB-003 |
| Unblocks | WEB-005 |
| Status | Kept in the [work package index](../README.md) |
| Requirements | ARC-03, ARC-07, A11Y-02, A11Y-03, SEC-10, UI-01 |
| Decisions | ADR-0002, ADR-0012, ADR-0014 (amendment of 2026-10-12), ADR-0019, ADR-0020 |
| Specs | [engine-protocol.md §14.1, §14.2, §14.3, §14.6, §14.7, §14.8 and §15](../../specs/engine-protocol.md#14-protocol-v1-the-agreed-changes) |

## Context

[CORE-013](CORE-013-protocol-v1-session-keys-and-vectors.md) switches the engine to protocol v1 as [spec §14](../../specs/engine-protocol.md#14-protocol-v1-the-agreed-changes) decided it, and ships the conformance vectors of [§15](../../specs/engine-protocol.md#15-conformance-vectors). This work package moves bayan-web to it, and so removes the web's side of the differences that the architecture review of 2026-11-20 lists in [H8](../../plan/reviews/2026-11-20.md#h8-the-shells-keep-diverging-while-the-protocol-work-of-h5-waits). At `bbba7da` the web sends twelve editing keys and the manifest's shortcuts, parsed from strings and matched against Command by a platform it guesses (`src/input/keys.ts`, `src/view/document-controller.ts`); names its platform `"web"`; counts its own restarts (`src/engine/recovery.ts`); flattens accessibility trees below level 64 without a node limit (`src/a11y/mirror.ts`); after a refused `hello` reports that the document could not be opened and carries on; never reads `v`, and checks only the envelope of what the worker sends (`src/engine/client.ts`); relies on tiles arriving in order with events (`src/view/compositor.ts`); computes the tile grid with a tolerance of 10⁻⁹ (`src/view/tiles.ts`); and starts the worker without the module's hash (`src/engine/start.ts`, [bayan-web issue 8](https://github.com/BayanDocs/bayan-web/issues/8)). [DESK-004](DESK-004-desktop-on-protocol-v1.md) does the same for the desktop, and [WEB-005](WEB-005-web-text-input-clipboard-and-a11y.md) follows with CORE-014's additions.

## Objective

bayan-web speaks protocol v1 as §14.1, §14.2, §14.3, §14.6, item 1 of §14.7 and §14.8 require, and its unit tests pass every `shell` and `web` case of the conformance vectors of its pinned core.

## Scope

### In scope

- **The pin:** `bayan-core.pin` moves to the commit that completes CORE-013, and `engine-package/` with it (`scripts/engine-package.sh`, `check:engine`); the generated protocol types follow.
- **Versions and the handshake (§14.1):** `hello` with `v: 1`, `platform` from the fixed list, as far as the browser tells it (`navigator.userAgentData.platform` where it exists, `navigator.platform` otherwise, `other` when neither says), and `runtime: "browser"`; `v` checked on every message but the reply to `hello`; every field the client and the controller read checked before use, which also closes the first review's open item that the client checks only the envelope ([L4](../../plan/reviews/2026-10-27.md#l4-latent-weaknesses-in-the-shells)); protocol violations ending the engine's use with §12.1's stop message and the worker terminated; a refused `hello` ending it as well, with the update prompt after `unsupported_protocol_version` (the app must be reloaded to finish an update, with a button that reloads the page); `engine_version` checked against its limit.
- **Restarts (§14.2):** the allowance of `recovery.ts` removed; the shell starts a new session when `engine.error` carries `restart`, tells the user "n of 3" from it in its live region, and stops, terminating the worker, on `restart: null`; §12.1's steps 2–4 unchanged.
- **Keys (§14.3):** `keys.ts` replaced by the spec's rule over the manifest's bindings, document keys and reserved keys; `preventDefault` exactly for the presses sent; no platform guessing for Ctrl and Command; Mod with `=`, `+`, `-` and `0` without Shift or Alt left to the browser's zoom; the clipboard keys left to the browser's clipboard events, as today; the manifest's labels shown where the interface shows shortcuts.
- **Revisions, invalidation and the tile grid (§14.6):** the compositor keeps a tile while no invalidation with a higher revision covers it, instead of counting invalidations per tile; tiles for a new scale requested by the compositor itself, since in a mode whose layout does not follow the window `view.set` no longer invalidates them, while in `web` mode the engine's invalidations after a new width or zoom say what to render again; `tiles.ts` computing exactly the spec's formula, its tolerance changed from 10⁻⁹ to 10⁻⁶.
- **Accessibility limits (§14.7 item 1):** the mirror's own flattening removed, because the engine now flattens; trees beyond the limits treated as protocol violations; a node with `child_count` mirrored with all its children, the parts it lacks loaded through `query.a11y { node, children: { start, count } }` when the mirror needs them (or earlier), without moving the focus.
- **The module's integrity (§14.8):** `start.ts` sends `wasm_integrity` with the module's SHA-384 from the build's manifest of engine files, so the worker's own request is checked; a test with a wrong hash shows that the engine does not start and the user is told.
- **Conformance vectors (§15):** unit tests that read `restart.json`, `tile-grid.json`, `a11y-limits.json` and `keys.json` from `engine-package/` (never a copy), run every case marked `shell` or `web`, and fail on a case they do not recognize.
- Comments, `AGENTS.md` and the docs repository's [bayan-web guide](../../developer/bayan-web.md), where they describe what changed (a linked docs pull request for the guide).

### Out of scope

- Replacing text, the caret, hit-testing, the clipboard messages and the accessibility tree's content (WEB-005); until then the web keeps pasting plain text as `input.text`.
- The service worker's checks of the worker's scripts (WEB-103).
- The manual passes of WEB-002's validation gate.

## Deliverables

- The changes above with their unit and end-to-end tests.
- Updated `AGENTS.md`, and a docs pull request for the developer guide.

## Acceptance criteria

- [ ] AC-1 The shell speaks v1: `hello` as §14.1 item 2 says, with unit tests for each platform the browser can report; messages with another `v`, and each other kind of violation of item 5, end the engine's use with the stop message and terminate the worker.
- [ ] AC-2 A refused `hello` ends the engine's use without a new `hello`; after `unsupported_protocol_version` the update prompt with its reload button is shown and announced in the live region, after any other error the stop message.
- [ ] AC-3 No restart counting is left in the shell; every `shell` case of `restart.json` passes, and the end-to-end tests of recovery (`diag.panic` with `test.allow_panic`) pass in Chromium, Firefox and WebKit, including the stop after the fourth failure.
- [ ] AC-4 Every `shell` and `web` case of `keys.json` passes in a unit test of the key decision, including the presses from Arabic, Russian, French and German layouts and with AltGr; an end-to-end test in each browser engine shows that the `keydown` events of Mod with `=`, `-` and `0` are not default-prevented and send no `input.key`, while Ctrl+B (Command+B on macOS) is default-prevented and sent.
- [ ] AC-5 Tiles are kept and replaced by revision, with a unit test in which a tile and an invalidation cross; every case of `tile-grid.json` passes.
- [ ] AC-6 Every `shell` case of `a11y-limits.json` passes; the mirror shows a node with more children than one message holds in full after loading its parts with `children` ranges, and axe's rules (WEB-003) stay green.
- [ ] AC-7 The worker starts only with a module whose hash matches `wasm_integrity`.
- [ ] AC-8 `pnpm verify` passes on Linux and both kinds of Mac in CI.

## Verification

`scripts/engine-package.sh` and `pnpm verify`; CI on Ubuntu 24.04, macOS 15 and macOS 26 (Intel).

## Notes and pitfalls

- `navigator.platform` is deprecated but still present everywhere; `navigator.userAgentData` exists only in Chromium. Neither is a security boundary: a wrong platform only changes which keys are bound.
- Keep the decision about each key synchronous, in the `keydown` handler: that is why the engine sends the lists in advance (§14.3).
- Loading left-out children must never replace the element that has focus (the first review's L4 names a related trap in `mirror.ts`).
- The size budgets of `pnpm verify` apply; the new code is small.

## Escalate if

- Any part of §14 cannot be built in one of the three browser engines as written.
- A browser does not let the page take a key that the manifest binds and the reserved table does not list, or delivers one the table lists.
