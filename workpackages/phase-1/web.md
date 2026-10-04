# Phase 1 — Faithful Viewer: web work packages (drafts)

**Status: Draft**, refined at the Phase-0 gate. All in bayan-web; attach bayan-web and docs (bayan-core read-only).

### WEB-101 — Viewer application
- **Size:** L · **Depends on:** WEB-002, CORE-125 · **Decisions:** ADR-0014, ADR-0019
- **Scope:** open local files (drag and drop, file picker, File System Access where available); engine worker; tile compositor with caching; page views and zoom; navigation pane; find; print and PDF export; consent prompts; interface strings through the engine; themes; responsive layout for tablets and phones (viewing).
- **Exit evidence:** Playwright end-to-end tests over public-corpus documents in three engines; bundle and performance budgets.

### WEB-102 — Accessibility mirror v1
- **Size:** L · **Depends on:** WEB-002, CORE-128 · **Decisions:** ADR-0020
- **Scope:** production accessibility DOM mirror from the real tree, with caret and selection sync; screen-reader navigation by headings, lists and tables; keyboard-only operation; axe checks in CI; manual screen-reader scripts.

### WEB-103 — PWA, offline and deployment
- **Size:** M · **Depends on:** WEB-101 · **Decisions:** ADR-0014, ADR-0026
- **Scope:** installable PWA with a hand-written service worker; offline viewing of local files; lazy font loading with integrity hashes; static-site deployment (a public demo on GitHub Pages) and a container image serving the app with the full security-header set; Subresource Integrity enforced; a "Source code" link to the exact source of the running version, configurable by operators (OPS-08).
