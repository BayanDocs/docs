# WEB-005: The web on protocol v1, part 2 — replacing text, the caret, hit-testing, the clipboard and accessible text

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | WEB / ACCESSIBILITY |
| Repository | bayan-web |
| Attach to session | bayan-web, bayan-core (read, for the WebAssembly package and its conformance vectors), docs |
| Size | L |
| Depends on | WEB-004, CORE-014 |
| Unblocks | WEB-101, WEB-102 |
| Status | Kept in the [work package index](../README.md) |
| Requirements | A11Y-02, A11Y-03, I18N-02, SEC-01, SEC-10, UI-01 |
| Decisions | ADR-0006, ADR-0012, ADR-0014 (amendment of 2026-10-12), ADR-0020, ADR-0021 |
| Specs | [engine-protocol.md §14.4, §14.5, §14.7 and §15](../../specs/engine-protocol.md#144-replacing-text-moving-the-caret-and-hit-testing) |

## Context

[CORE-014](CORE-014-protocol-v1-text-input-clipboard-and-a11y.md) adds to protocol v1 the messages for replacing text, moving the caret and hit-testing ([spec §14.4](../../specs/engine-protocol.md#144-replacing-text-moving-the-caret-and-hit-testing)), the clipboard in both directions ([§14.5](../../specs/engine-protocol.md#145-the-clipboard)), and the accessibility tree's language, direction, lines and selection ([§14.7](../../specs/engine-protocol.md#147-accessibility-trees-limits-and-content) item 2). Today the web's input bridges insert replacement text at the caret and leave the replaced range in place (`src/input/hidden-element-bridge.ts`, `src/input/edit-context-bridge.ts`), paste plain text as `input.text` and cannot copy, and the mirror marks the whole document as English, left to right ([H5](../../plan/reviews/2026-10-27.md#h5-the-engine-protocol-leaves-behavior-to-the-shells-and-they-already-decide-differently), [H8](../../plan/reviews/2026-11-20.md#h8-the-shells-keep-diverging-while-the-protocol-work-of-h5-waits)). This work package adds the new paths, after [WEB-004](WEB-004-web-on-protocol-v1.md) has moved the web to v1.

## Objective

bayan-web uses every addition of CORE-014: input methods, autocorrect and assistive technologies replace and select text through `input.text` and `input.select`, the clipboard works in both directions as raw bytes, and the accessibility mirror carries language, direction, lines and the selection from the engine.

## Scope

### In scope

- **The pin** moves to the commit that completes CORE-014, with `engine-package/` and the generated types.
- **Replacing text (§14.4):** both bridges send `input.text` with `replace` for an `EditContext` update range and for a `beforeinput` event's target ranges, mapped onto the mirrored node's text; deletions by word or line that the bridges forward as keys today (ADR-0014's amendment, design detail 4) become replacements where the browser gives their range.
- **The caret and selection (§14.4):** a selection that an assistive technology or the user makes in the mirror's editable element reaches the engine as `input.select`; the mirror shows the engine's `selection`.
- **Hit-testing (§14.4):** `query.hit` wherever the web needs the text position at a point and can wait for it.
- **Clipboard (§14.5):** `capabilities.clipboard_formats` from what the browser can exchange (`text/plain`, `text/html` and `image/png`, as each browser engine supports them); paste from the paste event's `clipboardData` as `input.paste` with raw UTF-8 or image bytes for the formats in both lists, replacing today's `input.text`; copy and cut from the copy and cut events through `clipboard.copy`, written with `navigator.clipboard.write` and promised `ClipboardItem` data during the event's user activation; the commands with `shell_action` from the interface doing the same; nothing decoded or sanitized by the browser on the way in (ADR-0006 decision 3).
- **Accessible text (§14.7 item 2):** `lang` and `dir` attributes on the mirror's elements, spans with `lang` (and `dir` where it differs) for `runs`, line breaks in the mirror where `line_starts` puts them, so that line-by-line reading follows the engine's lines; the document's `lang` and `dir` instead of the page's fixed English, left to right.
- **Conformance vectors (§15):** the new `shell` and `web` cases of CORE-014 in the unit tests.
- `AGENTS.md` and the docs repository's [bayan-web guide](../../developer/bayan-web.md) where they describe what changed (a linked docs pull request for the guide).

### Out of scope

- Real documents and editing (Phase 1 and Phase 2), the questions of [§14.9](../../specs/engine-protocol.md#149-still-open), and WEB-102's production mirror, which builds on this work.
- Turning the browser's own suggestions and spell checking back on in the bridges: proofing is the engine's (ADR-0022), and the editing protocol of Phase 2 decides whether the browser's suggestions may reach the document.
- The manual screen-reader and input-method passes of WEB-002's gate.

## Deliverables

- The changes above with unit tests and end-to-end tests in Chromium, Firefox and WebKit.
- Updated documentation, and a docs pull request for the developer guide.

## Acceptance criteria

- [ ] AC-1 A replacement through `EditContext` or through `beforeinput` reaches the engine as one `input.text` with `replace` and changes exactly that range, also for characters outside the Basic Multilingual Plane; the old text no longer stays next to the new.
- [ ] AC-2 A selection made in the mirror reaches the engine as `input.select`, and the mirror shows the engine's selection afterwards.
- [ ] AC-3 Paste sends `input.paste` with raw bytes of the formats both sides list, and copy and cut write the engine's items to the clipboard, in each browser engine as far as it supports the Clipboard API (end-to-end tests with clipboard permissions granted by Playwright where needed).
- [ ] AC-4 The mirror marks the mock document's Arabic paragraph `dir="rtl"` with its language, its run in another language as a span with `lang`, and breaks its lines where `line_starts` says; axe's rules (WEB-003) stay green.
- [ ] AC-5 The new conformance cases pass, and `pnpm verify` passes on Linux and both kinds of Mac in CI.

## Verification

`scripts/engine-package.sh` and `pnpm verify`; CI on Ubuntu 24.04, macOS 15 and macOS 26 (Intel).

## Notes and pitfalls

- Safari accepts `navigator.clipboard.write` only during the user's action and with promised data; Firefox supports `ClipboardItem` only in recent versions. Write to the clipboard inside the copy or cut event, and test each engine.
- `getTargetRanges()` of `beforeinput` returns ranges in the hidden element's text; map them through the text the bridge mirrors, as the bridges already do for the caret.
- The mirror is invisible; line breaks that it inserts must not change the text a screen reader reads as words.

## Escalate if

- One of the browser engines cannot provide what §14.4, §14.5 or §14.7 need, or cannot give the clipboard's bytes without decoding them.
