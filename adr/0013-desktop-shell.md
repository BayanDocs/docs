# ADR-0013: Desktop shell — Qt 6 Quick with thin C++

- **Status:** Accepted — validation gate (DESK-002)
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

## Revisit when

DESK-002 fails on accessibility or input methods; CXX-Qt reaches a stable 1.0; or Qt's licensing changes for the modules we use.
