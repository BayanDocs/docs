# DESK-001: Desktop scaffold and CI

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | DESKTOP |
| Repository | bayan-desktop |
| Attach to session | bayan-desktop, docs (and bayan-core read-only, for the C header once CORE-007 lands) |
| Size | M |
| Depends on | — (uses a stub engine until CORE-007's C SDK exists) |
| Unblocks | DESK-002, X-003 |
| Status | Ready |
| Requirements | ARC-03, ARC-04, PLT-01 |
| Decisions | ADR-0013 (implement it), ADR-0012, ADR-0017, ADR-0003 (LGPL compliance) |
| Specs | [engine-protocol.md §3](../../specs/engine-protocol.md#3-transport) |

## Context

The desktop shell is a thin Qt 6 Quick application around the engine's C ABI. ADR-0013 fixes Qt 6 (starting on 6.12, the newest minor at planning time), Qt Quick for the interface, C++20, CMake, LGPLv3 modules only, and no C++ dependencies other than Qt. This work package creates the project, its build and test infrastructure, and a stub of the engine interface so development can proceed before the real engine SDK exists.

## Objective

A buildable, tested Qt Quick application skeleton on Windows, macOS and Linux with CI, strict compiler and lint settings, a forbidden-module check, and an engine integration layer that works with a stub or with the CORE-007 SDK.

## Scope

### In scope

- CMake project with `CMakePresets.json` (configure, build, test and workflow presets for Windows MSVC, macOS and Linux), C++20, warnings as errors, a minimum CMake version recorded in the pull request.
- Qt pinned to an exact 6.12.x version (at least 24 hours old) installed in CI with aqtinstall at a pinned version (checksums verified); local setup notes for each OS.
- Application skeleton in Qt Quick: main window, placeholder ribbon area, placeholder document area, light and dark themes following the system.
- Engine integration layer in `src/engine/`: a C++ RAII wrapper over the C ABI from `specs/engine-protocol.md`; message posting and a callback that marshals events to the main thread; a **stub implementation** of the same C header (selected with a CMake option such as `BAYAN_ENGINE=stub|sdk`) that returns a fixed test tile; when built against the CORE-007 SDK, the real engine is linked and its tile shown.
- `clang-format` and `clang-tidy` configurations and CI checks.
- Qt Test unit tests for the engine wrapper (using the stub).
- CI matrix: Windows (MSVC), macOS (arm64) and Linux; build, test, and a headless smoke test that launches the app with the offscreen platform plugin, renders the stub page, and exits.
- AddressSanitizer and UndefinedBehaviorSanitizer build and test job on Linux.
- A CMake-level check that fails configuration if a GPL-only or commercial-only Qt module from ADR-0013's list is linked.
- A verification entry point (`cmake --workflow --preset verify` or a script) documented in this repository's `AGENTS.md`.

### Out of scope

The document canvas, input methods and accessibility (DESK-002); packaging (DESK-104).

## Deliverables

Project, CI workflows, tests, updated `AGENTS.md` and `README.md`.

## Acceptance criteria

- [ ] AC-1 CI is green on Windows, macOS and Linux, including the headless smoke test.
- [ ] AC-2 The sanitizer job runs the tests cleanly.
- [ ] AC-3 Linking a forbidden Qt module fails configuration (demonstrated).
- [ ] AC-4 The app builds and runs against the stub and, if the CORE-007 SDK artifact is available, against the real engine.
- [ ] AC-5 Qt version, aqtinstall version and all tool versions are pinned, at least 24 hours old, and recorded in the pull request.

## Verification

The repository's verify workflow; CI links.

## Notes and pitfalls

- Use `qmlcachegen`, not the commercial `qmlsc`.
- Link Qt dynamically on every platform (LGPL compliance).

## Escalate if

A required Qt feature is only available in a GPL-only or commercial module.
