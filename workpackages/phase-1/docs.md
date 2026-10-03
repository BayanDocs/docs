# Phase 1 — Faithful Viewer: documentation work packages (drafts)

**Status: Draft**, refined at the Phase-0 gate. All in docs.

### DOCS-101 — Viewer user guide and release-notes process
- **Size:** M · **Depends on:** DESK-101, WEB-101
- **Scope:** `handbook/` pages for installing and using the viewer on desktop and web, privacy and security behavior (external content prompts), font availability and the Fidelity Inspector; a release-notes template that includes fidelity scores and layout-epoch changes.

### DOCS-102 — Living architecture and API reference
- **Size:** M · **Depends on:** CORE-125
- **Scope:** "How the engine works" pages kept current with the code (model, layout pipeline, rendering, protocol); published rustdoc for core and server and TypeScript declarations for the protocol, linked from the site.

### DOCS-103 — Word Behavior Notes publication
- **Size:** S · **Depends on:** LAB-102…LAB-105
- **Scope:** make the Word Behavior Notes a first-class, browsable section of the site with an index by feature, so they become a public commons for everyone implementing OOXML.
