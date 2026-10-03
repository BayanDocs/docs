# DESK-002: Spike — Qt Quick document canvas, input and accessibility

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | DESKTOP / A11Y-I18N |
| Repository | bayan-desktop |
| Attach to session | bayan-desktop, docs (bayan-core read-only) |
| Size | L |
| Depends on | DESK-001, CORE-007 |
| Unblocks | DESK-101, DESK-103 |
| Status | Ready |
| Requirements | A11Y-02, I18N-07, PERF-04 |
| Decisions | ADR-0013 (this spike is its validation gate), ADR-0012, ADR-0020 |
| Specs | [engine-protocol.md](../../specs/engine-protocol.md) |

## Context

The riskiest parts of the desktop shell are the custom document canvas (tiles from the engine, smooth at high DPI), input methods for East Asian languages, and exposing canvas text to screen readers. Research on 2026-10-03 confirms Qt supports custom accessible text interfaces (registered with `QAccessible::installFactory`) mapped to UI Automation, NSAccessibility and AT-SPI2. This spike proves all three against the CORE-007 mock document.

## Objective

Demonstrate smooth tiled rendering, working IME composition and screen-reader access for an engine-drawn canvas on Windows, macOS and Linux, and report measurements and recommendations.

## Scope

### In scope

- `DocumentCanvas` (`QQuickItem`): computes visible tiles for the viewport, zoom and device pixel ratio; requests them from the engine; caches them as scene-graph textures; scrolls and zooms smoothly (trackpad, wheel, pinch, keyboard), showing scaled stale tiles until fresh ones arrive; handles fractional scaling on Windows and Retina on macOS; draws overlays (caret, selection) from `overlay.update`.
- Input: keyboard events to `input.key`; IME through `inputMethodQuery` (cursor rectangle, surrounding text, cursor position, enabled state) and `inputMethodEvent` (pre-edit and commit) mapped to `input.composition` and `input.text`.
- Accessibility: a custom accessible interface for the canvas implementing text and editable-text interfaces over the engine's mock accessibility tree (text by offset, caret offset, selections, character rectangles, attributes where available), registered through a factory.
- Manual test scripts and results: Japanese, Chinese and Korean input on Windows and macOS (and IBus or Fcitx on Linux if feasible); NVDA or Narrator on Windows, VoiceOver on macOS, Orca on Linux reading the mock document.
- Measurements: frame times while scrolling and zooming, tile request latency, memory use.
- Report (`docs/spikes/DESK-002-report.md` in this repository) and a docs pull request updating ADR-0013's validation status.

### Out of scope

Real documents, editing, printing, the ribbon.

## Deliverables

Canvas item, input and accessibility bridges (prototype quality but structured for reuse), test scripts, recordings or screenshots, report.

## Acceptance criteria

- [ ] AC-1 Scrolling and zooming stay at the display refresh rate on reference hardware for the mock document (frame-time figures in the report).
- [ ] AC-2 Japanese, Chinese and Korean composition text appears in the engine's editable line on Windows and macOS (evidence: screenshots or short recordings).
- [ ] AC-3 A screen reader reads the mock document's text on Windows and macOS (evidence and test script); Linux result reported.
- [ ] AC-4 No document logic was added to the shell.
- [ ] AC-5 Report with measurements and recommendations delivered.

## Verification

The repository's verify workflow; report evidence.

## Escalate if

Qt's accessibility or input-method APIs cannot express what the engine needs; the planner will decide whether ADR-0013 needs amendment.
