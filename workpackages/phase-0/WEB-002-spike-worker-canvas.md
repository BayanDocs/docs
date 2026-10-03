# WEB-002: Spike — worker canvas, input bridge and accessibility mirror

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | WEB / A11Y-I18N |
| Repository | bayan-web |
| Attach to session | bayan-web, docs (bayan-core read-only) |
| Size | L |
| Depends on | WEB-001, CORE-007 |
| Unblocks | WEB-101, WEB-102 |
| Status | Ready |
| Requirements | A11Y-02, I18N-07, PERF-04, PERF-06 |
| Decisions | ADR-0014 (this spike is its validation gate), ADR-0012, ADR-0020 |
| Specs | [engine-protocol.md](../../specs/engine-protocol.md) |

## Context

Drawing the document on a canvas gives identical layout to desktop, but browsers then provide neither text input nor accessibility for free. ADR-0014 plans EditContext where available (Chromium only as of 2026-10-03), a hidden editable-element fallback elsewhere, and an off-screen DOM mirror for screen readers. This spike proves the architecture against the CORE-007 mock document.

## Objective

Demonstrate worker-rendered tiles composited smoothly on the main thread, IME composition through both input-bridge implementations, and a screen reader reading the accessibility mirror, in Chromium, Firefox and WebKit, with measurements.

## Scope

### In scope

- Load the CORE-007 WebAssembly package in a module worker through its worker host; implement the main-thread side of the protocol (typed with the generated TypeScript declarations).
- Tile compositor: a Canvas 2D compositor drawing transferred `ImageBitmap` tiles; scroll and zoom; device-pixel-ratio changes; stale-tile scaling until fresh tiles arrive; overlays for caret and selection.
- `InputBridge` interface with two implementations: **EditContext** (Chromium) and a **hidden editable element** positioned at the caret (Firefox, Safari). Handle keyboard shortcuts, composition events, `beforeinput` types (`insertText`, `deleteContentBackward`, `insertReplacementText`, `insertFromPaste`, …) and clipboard events, translating them to engine messages.
- Accessibility mirror v0: an off-screen DOM built from the mock accessibility tree (heading, paragraphs, list, table) with appropriate roles; a prototype of keeping the screen reader's position in sync with the engine caret.
- Tests: Playwright tests for tile rendering, scrolling and zooming in three engines; a Chromium DevTools-protocol IME composition test; manual screen-reader scripts and results (NVDA with Firefox or Chrome; VoiceOver with Safari).
- Measurements: keydown → overlay update → paint latency; frame times while scrolling; worker message latency; memory.
- Report (`docs/spikes/WEB-002-report.md` in this repository) and a docs pull request updating ADR-0014's validation status.

### Out of scope

Real documents, editing, the ribbon, PWA features.

## Deliverables

Worker integration, compositor, input bridges, accessibility mirror prototype, tests, report.

## Acceptance criteria

- [ ] AC-1 Smooth scrolling and zooming in Chromium, Firefox and WebKit (frame-time figures).
- [ ] AC-2 Japanese, Chinese and Korean composition reaches the engine through EditContext (Chromium) and through the fallback (Firefox and Safari), with evidence.
- [ ] AC-3 A screen reader reads the mirror's text in at least two browser/screen-reader combinations, with evidence.
- [ ] AC-4 Keystroke-to-overlay latency is reported, with a plan to meet PERF-04 if it is not met.
- [ ] AC-5 The CSP and Trusted Types configuration from WEB-001 is unchanged (no relaxations).

## Verification

`pnpm verify`; Playwright results; report evidence.

## Escalate if

Any browser blocks a required capability under our security headers, or the input-bridge approach fails for a major input method.
