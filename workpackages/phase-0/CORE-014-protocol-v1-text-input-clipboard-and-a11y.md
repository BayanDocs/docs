# CORE-014: Engine protocol v1, part 2 — replacing text, the caret, hit-testing, the clipboard and accessible text

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | UI / engine |
| Repository | bayan-core, and a small docs pull request that marks the items implemented |
| Attach to session | bayan-core, docs; bayan-desktop and bayan-web read-only |
| Size | L |
| Depends on | CORE-013 |
| Unblocks | DESK-005, WEB-005, CORE-125 |
| Status | Kept in the [work package index](../README.md) |
| Requirements | ARC-03, ARC-07, A11Y-02, I18N-02, SEC-01 |
| Decisions | ADR-0006, ADR-0012, ADR-0020, ADR-0021 |
| Specs | [engine-protocol.md §14.4, §14.5, §14.7 and §15](../../specs/engine-protocol.md#144-replacing-text-moving-the-caret-and-hit-testing) |

## Context

[CORE-013](CORE-013-protocol-v1-session-keys-and-vectors.md) switches the engine to protocol v1 with every change that is not additive. This work package adds the rest of [spec §14](../../specs/engine-protocol.md#14-protocol-v1-the-agreed-changes), which only adds to v1 (§9): the text positions and messages that let input methods, autocorrect and screen readers replace text and move the caret (§14.4), the clipboard in both directions as raw bytes (§14.5), and the content of the accessibility tree that screen readers need, language, direction, lines and the selection (§14.7 item 2). The gaps come from the DESK-002 and WEB-002 spikes and from the architecture reviews' [H5](../../plan/reviews/2026-10-27.md#h5-the-engine-protocol-leaves-behavior-to-the-shells-and-they-already-decide-differently) and [H8](../../plan/reviews/2026-11-20.md#h8-the-shells-keep-diverging-while-the-protocol-work-of-h5-waits). Everything works on the mock document, whose editable line is the only editable text until Phase 2.

## Objective

The engine implements §14.4, §14.5 and item 2 of §14.7 on the mock document, additively to v1, with conformance cases for what a shell can check without a platform.

## Scope

### In scope

- **Text input (§14.4):** `input.text` with `replace`; `input.select`, with its errors; `query.hit`, with `caret` and `character`. The mock document's editable line gains a selection: `input.select` sets it, Shift with ArrowLeft, ArrowRight, Home and End extends it, typing, Backspace and Delete replace it, and `overlay.update` draws it.
- **Clipboard (§14.5):** `welcome.clipboard_formats` (`text/plain`), `input.paste` (the richest format the engine reads inserted at the selection; formats the engine does not read ignored; the mock's limits for its editable text kept), and `clipboard.copy` with `cut` (the selection of the editable line as `text/plain`; empty items when nothing is selected).
- **Accessible text (§14.7 item 2):** `lang` and `dir` on every node that sets them and always on the document node, `runs`, `line_starts`, and `selection` in replies to `query.a11y` and in `a11y.update`. The mock document gains one right-to-left paragraph in Arabic with a run in another language, so that both shells can test language, direction and runs end to end; its text is drawn as bars like the rest until the text pipeline exists.
- Conformance cases (§15) for replacing text and for the selection where a shell's side can be checked without a platform, for example the `input.text` a shell sends for a given platform range in a given mirrored text; and `engine` cases for the same.
- The schema and TypeScript declarations regenerated, the fuzz targets' seeds and dictionaries extended, `bayan-engine`'s documentation, and a docs pull request that marks the items implemented in the spec's status line.

### Out of scope

- Real documents and real editing (CORE-125, Phase 2), `text/html` for copying (CORE-125), and the questions of [§14.9](../../specs/engine-protocol.md#149-still-open).
- Any change in the shells (DESK-005, WEB-005).
- Any change that is not additive to v1; if one turns out to be needed, escalate.

## Deliverables

- The messages, fields and mock-document behavior above, with tests, in `bayan-engine`, and the regenerated schema and declarations.
- The new conformance cases in the files of `crates/bayan-engine/protocol/conformance/`.
- The docs pull request.

## Acceptance criteria

- [ ] AC-1 `input.text` with `replace` replaces exactly the range, the caret ending after the new text; an unknown node is `not_found`, and a range outside the node's text, in a node that is not editable, or with an end inside a surrogate pair is `invalid_request`; tests cover each, with and without an `id`.
- [ ] AC-2 `input.select` sets a caret or a selection on the editable line, and the engine answers with `overlay.update` and `a11y.update`; its errors are those of AC-1; Shift with the arrows, Home and End extends it; typing, Backspace and Delete replace it.
- [ ] AC-3 `query.hit` returns `caret` and `character` as §14.4 says, and `null` off the pages; tests on both halves of a character, in left-to-right and right-to-left text, between lines and between pages.
- [ ] AC-4 `input.paste` and `clipboard.copy` work as §14.5 says, raw bytes in and out, and the engine reads only the formats it lists in `welcome`.
- [ ] AC-5 Every node of the mock's tree has its language and direction (inherited or its own), the Arabic paragraph is `rtl` with its run in another language, `line_starts` match the mock's lines, and the selection appears in both kinds of message.
- [ ] AC-6 Every change is additive to CORE-013's v1 (§9): only new messages and new optional fields, so every message that CORE-013's engine accepted keeps its meaning; CORE-013's protocol tests pass unchanged, except where an expected message gains one of the new fields.
- [ ] AC-7 The new conformance cases pass in bayan-core's tests; `cargo xtask verify` passes; no dependency is added (or each is justified); the docs pull request is open and linked.

## Verification

`cargo xtask verify`; the docs pull request passes `scripts/verify.sh`.

## Notes and pitfalls

- Offsets are UTF-16 code units and never fall inside a surrogate pair (§7); the mock's editable line counts characters internally today, so convert at the boundary and test with characters outside the Basic Multilingual Plane.
- Clipboard bytes are untrusted input like any blob: the engine reads `text/plain` as UTF-8 with its usual limits and replaces what is not valid.
- Do not let the new paragraph change the pages of the mock document more than necessary: the shells' tests compare pixels and positions, and DESK-005 and WEB-005 update them.

## Escalate if

- A part of §14.4, §14.5 or §14.7 cannot be built as written, or would need a change that is not additive to v1.
- A new dependency seems necessary.
