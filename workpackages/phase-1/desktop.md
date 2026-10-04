# Phase 1 — Faithful Viewer: desktop work packages (drafts)

**Status: Draft**, refined at the Phase-0 gate. All in bayan-desktop; attach bayan-desktop and docs (bayan-core read-only).

### DESK-101 — Viewer application
- **Size:** L · **Depends on:** DESK-002, CORE-125 · **Decisions:** ADR-0013, ADR-0019
- **Scope:** document windows; open dialogs, recent files, drag and drop, file associations; page views (single, multiple, zoom levels, fit width); navigation pane (headings, page thumbnails); find bar; status bar (pages, words, font availability, fidelity notices); consent prompts for external content; settings; interface strings through the engine (Fluent); light, dark and high-contrast themes.
- **Exit evidence:** end-to-end tests opening public-corpus documents; manual test script results on three platforms.

### DESK-102 — Printing path
- **Size:** M · **Depends on:** DESK-101, CORE-121 · **Decisions:** ADR-0011
- **Scope:** render display lists to `QPrinter` as vector output with exact glyph positions on Windows, macOS and Linux; print preview; page ranges and scaling options; "print to PDF" uses the engine's PDF export.

### DESK-103 — Accessibility bridge v1
- **Size:** M · **Depends on:** DESK-002, CORE-128 · **Decisions:** ADR-0020
- **Scope:** production accessibility interfaces over the real accessibility tree; navigation by headings, lists and tables in NVDA, JAWS, Narrator, VoiceOver and Orca; keyboard-only operation of the viewer; automated accessibility-tree assertions.

### DESK-104 — Packaging, signing and update channel v1
- **Size:** L · **Depends on:** DESK-101, X-101 · **Decisions:** ADR-0026
- **Scope:** Windows installer (MSIX or MSI, decided here) signed; macOS universal or per-architecture app signed and notarized; Linux Flatpak (Flathub submission), AppImage, `.deb` and `.rpm`; bundled fonts and optional packs; update mechanism per ADR-0026; reproducible-build investigation.
- **Note (2026-10-04):** also ship the third-party notices for the code that Qt bundles in its libraries and for ICU on Linux, taken from the SBOM files of the Qt release being packaged, for example the FreeType and Independent JPEG Group credits ([ADR-0017](../../adr/0017-supply-chain-and-dependency-policy.md), amendment "what the license allowlist covers").
