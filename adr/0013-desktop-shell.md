# ADR-0013: Desktop shell — Qt 6 Quick with thin C++

- **Status:** Accepted — validation gate (DESK-002) open: canvas and bridges built and tested automatically on 2026-10-12; manual tests on Windows, macOS and Linux deferred by the owner on 2026-10-14
- **Date:** 2026-10-03
- **Deciders:** Planner (the owner specified C++ and Qt)
- **Related:** ARC-03, ARC-04, UI-01…UI-09, A11Y-02, PLT-01, ADR-0012, ADR-0019, DESK-001, DESK-002

## Context

The desktop application must start instantly, use little memory, work offline, integrate with Windows, macOS and Linux (accessibility, input methods, printing, file associations), and look modern, including a ribbon in Classic mode and a near-empty Focus mode. The owner chose C++ and Qt. Facts verified on 2026-10-03:

- **Qt 6.12** was released on 2026-09-30 and is a long-term-support (LTS) line; Qt 6.8 is the previous LTS. For open-source users, LTS patch releases are published openly only until the next minor release; later LTS patches have appeared as open source roughly a year after their commercial release.
- **Module licenses:** Qt Quick/QML, Quick Controls, Quick Dialogs, Widgets, SVG, Multimedia, TextToSpeech, PDF and Protobuf are available under LGPLv3. Charts, Graphs, GRPC, Quick 3D, Virtual Keyboard and Canvas Painter are GPLv3 or commercial only. The `qmlsc` compiler is commercial-only; `qmlcachegen` is open.
- **Accessibility:** Qt uses UI Automation (with a text pattern) on Windows, NSAccessibility on macOS and AT-SPI2 on Linux; Qt 6.11 improved AT-SPI support for Orca. A custom-drawn canvas can expose text through a custom `QAccessibleObject` implementing the text and editable-text interfaces, registered with `QAccessible::installFactory`.

## Decision

1. **Qt 6, starting on 6.12**, built with **CMake** (presets, version pinned in CI) and **C++20**.
2. **Qt version policy:** because open-source LTS patches stop at the next minor release, BayanDocs tracks the **newest Qt 6 minor release**, moving in a batched dependency session once that minor's first patch release (x.y.1) is at least 24 hours old. The exact version is pinned in CI and in packaging.
3. **Qt Quick (QML) for the interface**, generated from the shared UI manifest (ADR-0019); **C++ only as glue**: engine binding, document canvas item, input-method bridge, accessibility bridge, printing, platform integration. No document logic in the shell.
4. **Only LGPLv3 Qt modules**, dynamically linked. GPL-only modules and commercial-only tools are prohibited. `qmlcachegen` (not `qmlsc`) compiles QML.
5. **No C++ dependencies besides Qt** (Qt Test for tests). Anything else needs an ADR amendment.
6. **Document canvas:** a custom `QQuickItem` that composites engine-rendered tiles as scene-graph textures, draws overlays, implements `inputMethodQuery`/`inputMethodEvent` for IMEs, and exposes the engine's accessibility tree through custom `QAccessible` interfaces.
7. **Printing** renders display lists to `QPrinter` as vector output (DESK-102). Print dialogs may use Qt Widgets (LGPL).

## Consequences

- The shell stays small; nearly all behavior lives in the core and is shared with the web.
- Qt Quick enables a polished, animated, themeable interface and keeps a future tablet shell possible.
- Tracking the newest minor release means a Qt upgrade every six months or so, handled in batched sessions.

## Alternatives considered

- **Qt Widgets for the interface:** mature, but less flexible for a modern ribbon and Focus mode, and in maintenance mode. Used only for platform dialogs where helpful.
- **CXX-Qt (QML with Rust backends instead of C++):** removes a language, but is in early development with frequent API changes; revisit later.
- **Electron or Tauri reusing the web interface:** one interface codebase, but higher memory use (Electron), weaker native integration, and contrary to the owner's choice.
- **Rust-native GUI toolkits (Slint, iced, egui, Xilem):** accessibility, input methods and printing are less mature than Qt's.

## Validation gate

DESK-002 must demonstrate smooth scrolling and zooming of engine tiles at high DPI on all three platforms, working IME composition (Japanese, Chinese, Korean) into the engine, and a screen reader reading text from the canvas on at least Windows (NVDA or Narrator) and macOS (VoiceOver).

## Validation result (DESK-002, 2026-10-12)

DESK-002 ([bayan-desktop#6](https://github.com/BayanDocs/bayan-desktop/pull/6)) built the document canvas, the input-method bridge and the accessibility bridge, and tested them automatically against CORE-007's engine, which CI now builds from a pinned bayan-core commit on Linux, macOS and Windows. The gate is not passed yet: its manual tests on Windows, macOS and Linux remain, and the work package's report lists them with scripts.

- **Tiles at high DPI:** the canvas places engine tiles on whole device pixels; automated tests compare nine pixels of a page (a 3 × 3 grid) with the engine's own rendering of each. CI runs them at 100 % and 125 % scaling on all three platforms; during the work package they also ran once at 150 % and 200 %, and the smoke test at 175 % and 300 %. Without a graphics card, with Qt's OpenGL path on an emulated GPU at 60 Hz, scrolling and zooming had no late frames at 100 % and 5 of 642 at 125 %. Frame times on the reference laptops, and on Linux at high DPI, are pending (AC-1; this gate asks for all three platforms).
- **Input methods:** Japanese, Chinese and Korean composition reaches the engine's editable line when the event sequences that Qt's Windows, macOS and IBus integrations send are replayed. Ending a composition early (a click, Tab, another app) needs Windows' input context to be reset, which commits it; the canvas does so, tested with a replay of what Windows does. The real input methods on Windows and macOS are pending (AC-2).
- **Screen readers:** the canvas exposes the engine's accessibility tree as one multi-line editable text, with the caret, character positions, change events and editing at the caret, as Qt's platform bridges ask for them. On Linux, read through Qt's AT-SPI bridge with AT-SPI's own tools, it gave the document's text, the caret and the character positions, and editing through it reached the engine. NVDA or Narrator, VoiceOver and Orca are pending: this gate asks for Windows and macOS, and the work package's AC-3 for the Linux result, whatever it is.
- **Qt's interfaces** (`QQuickItem`, the scene graph, `inputMethodQuery` and `inputMethodEvent`, `QAccessible` factories and the text, editable-text and action interfaces) expressed everything the engine offers, so the decision needs no amendment. The gaps found are in engine protocol v0, which has no message for replacing text near the caret, hit-testing or moving the caret to an offset, and no selection or line ranges in its accessibility tree; the report recommends them for the protocol's next version.

The planner marks the gate passed or failed once the owner's results of the manual tests are recorded in the report.

**2026-10-14:** the owner deferred the manual tests and had DESK-002 merged (bayan-desktop#6 as a001348), so that the desktop work packages that build on it, DESK-101 and DESK-103, can start. DESK-002 is marked Done with AC-1 to AC-3 open, as WEB-002 was with its manual passes outstanding. The gate stays open until the manual tests are run; their script is [`docs/spikes/DESK-002-manual-tests.md`](https://github.com/BayanDocs/bayan-desktop/blob/main/docs/spikes/DESK-002-manual-tests.md) in bayan-desktop.

## Revisit when

DESK-002 fails on accessibility or input methods; CXX-Qt reaches a stable 1.0; or Qt's licensing changes for the modules we use.

## Amendment (2026-10-04)

The desktop app is now licensed GPL-3.0-or-later (ADR-0003). GPL-only Qt modules would therefore be license-compatible, but the LGPL-only rule stays: GPL-only Qt modules would block the proposed app-store permission (ADR-0003 §4) and remove the flexibility of dynamic linking. No other part of this decision changes.
