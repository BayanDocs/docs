# DESK-005: The desktop on protocol v1, part 2 — replacing text, the caret, hit-testing, the clipboard and accessible text

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | DESKTOP / ACCESSIBILITY |
| Repository | bayan-desktop |
| Attach to session | bayan-desktop, bayan-core (read, for the SDK and its conformance vectors), docs |
| Size | L |
| Depends on | DESK-004, CORE-014 |
| Unblocks | DESK-101, DESK-103 |
| Status | Kept in the [work package index](../README.md) |
| Requirements | A11Y-02, A11Y-03, I18N-02, SEC-01, UI-01 |
| Decisions | ADR-0006, ADR-0012, ADR-0013, ADR-0020, ADR-0021 |
| Specs | [engine-protocol.md §14.4, §14.5, §14.7 and §15](../../specs/engine-protocol.md#144-replacing-text-moving-the-caret-and-hit-testing) |

## Context

[CORE-014](CORE-014-protocol-v1-text-input-clipboard-and-a11y.md) adds to protocol v1 the messages for replacing text, moving the caret and hit-testing ([spec §14.4](../../specs/engine-protocol.md#144-replacing-text-moving-the-caret-and-hit-testing)), the clipboard in both directions ([§14.5](../../specs/engine-protocol.md#145-the-clipboard)), and the accessibility tree's language, direction, lines and selection ([§14.7](../../specs/engine-protocol.md#147-accessibility-trees-limits-and-content) item 2). The desktop has none of these paths today: it replaces text near the caret by sending one Backspace or Delete per character (`deleteAroundCaret` in `src/canvas/documentcanvas.cpp`), cannot paste or copy and announces no clipboard formats (`src/app/documentsession.cpp`), and its accessible text has no language, direction, lines or selection from the engine ([H5](../../plan/reviews/2026-10-27.md#h5-the-engine-protocol-leaves-behavior-to-the-shells-and-they-already-decide-differently), [H8](../../plan/reviews/2026-11-20.md#h8-the-shells-keep-diverging-while-the-protocol-work-of-h5-waits)). This work package adds them, after [DESK-004](DESK-004-desktop-on-protocol-v1.md) has moved the desktop to v1.

## Objective

bayan-desktop uses every addition of CORE-014: input methods, autocorrect and screen readers replace and select text through `input.text` and `input.select`, the clipboard works in both directions as raw bytes, and the accessibility bridge exposes language, direction, lines and the selection from the engine.

## Scope

### In scope

- **The pin** moves to the commit that completes CORE-014, with the header and schema copies and the stub engine following as far as the shell's tests use the new messages.
- **Replacing text (§14.4):** input-method replacements (`QInputMethodEvent`'s replacement range, converted from the caret-relative range Qt gives into the mirrored node's offsets) and the editable-text interface's `insertText`, `deleteText` and `replaceText` send `input.text` with `replace`; `deleteAroundCaret` and its key presses removed.
- **The caret and selection (§14.4):** `setCursorPosition`, `setSelection`, `addSelection` and `removeSelection` of Qt's text interface send `input.select`; `selection`, `selectionCount` and the caret answer from the engine's tree.
- **Hit-testing (§14.4):** `offsetAtPoint` answered from the tree's character boxes, as the spec allows for interfaces that must answer at once; `query.hit` used wherever an answer can wait.
- **Clipboard (§14.5):** `capabilities.clipboard_formats` listing what the shell can exchange through `QClipboard` as raw bytes; the platform's copy, cut and paste (`QKeySequence::Copy`, `Cut` and `Paste`, and the commands with `shell_action` from menus or the ribbon) sending `clipboard.copy` and `input.paste`; `QMimeData` read and written with `data()` and `setData()` for the formats in both lists only, text converted to UTF-8 and otherwise untouched, nothing decoded by Qt (ADR-0006 decision 3).
- **Accessible text (§14.7 item 2):** the text interface's attributes (`attributes()`, with the language and the writing direction of each run) and line boundaries (`textAtOffset` and its neighbours with `LineBoundary`) from `lang`, `dir`, `runs` and `line_starts`; the canvas's text direction from the document node's `dir`.
- **Conformance vectors (§15):** the new `shell` and `desktop` cases of CORE-014 in the unit tests.
- `AGENTS.md`, `src/engine/README.md` and the docs repository's [bayan-desktop guide](../../developer/bayan-desktop.md) where they describe what changed (a linked docs pull request for the guide).

### Out of scope

- Real documents and editing (Phase 1 and Phase 2), the questions of [§14.9](../../specs/engine-protocol.md#149-still-open), and DESK-103's production accessibility bridge, which builds on this work.
- The manual screen-reader and input-method passes of DESK-002's gate; this work package's tests drive Qt's interfaces as DESK-002's do.

## Deliverables

- The changes above, with unit tests and canvas tests against the stub and the real engine.
- Updated documentation, and a docs pull request for the developer guide.

## Acceptance criteria

- [ ] AC-1 A replacement by an input method or through `replaceText` reaches the engine as one `input.text` with `replace` and changes exactly that range, also for characters outside the Basic Multilingual Plane; no Backspace or Delete is sent for it.
- [ ] AC-2 Setting the caret or a selection through Qt's text interface reaches the engine as `input.select`, and the interface reports the engine's selection afterwards.
- [ ] AC-3 `offsetAtPoint` gives the character whose box holds the point and -1 elsewhere, in agreement with `query.hit`'s `exact` for the same points (a test against the real engine).
- [ ] AC-4 Copy, cut and paste work through `QClipboard` with the formats that both sides list, as raw bytes, from the keys and from the commands with `shell_action`; a test shows that a format the engine does not list is not read.
- [ ] AC-5 Qt's text attributes and line boundaries for the mock document's Arabic paragraph report `rtl`, its language and its run in another language, and lines as `line_starts` gives them.
- [ ] AC-6 The new conformance cases pass, and `cmake --workflow --preset verify`, the jobs against the real engine and the sanitizer jobs pass on all three platforms.

## Verification

`cmake --workflow --preset verify`; `scripts/build-engine-sdk.sh` and `scripts/test-engine-sdk.sh --sdk build/bayan-core-sdk --sanitizers`; CI on Linux, macOS and Windows.

## Notes and pitfalls

- Qt's input-method replacement range is relative to the cursor and counts UTF-16 code units of the text the shell reported through `inputMethodQuery`; convert it to the node's offsets with the same mirrored text, and test it with surrogate pairs.
- `QClipboard` on Linux has two clipboards; only the standard one (`QClipboard::Clipboard`) is in scope, and the selection clipboard of the middle mouse button stays out until an editing work package decides it.
- Never log clipboard contents or text (AGENTS.md §6).

## Escalate if

- One of Qt's interfaces cannot express what §14.4, §14.5 or §14.7 provide on one of the three platforms.
- A platform clipboard offers a format the engine lists only in a form that the shell would have to decode.
