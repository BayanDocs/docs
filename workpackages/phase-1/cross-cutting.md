# Phase 1 — Faithful Viewer: cross-repository work packages (drafts)

**Status: Draft**, refined at the Phase-0 gate.

### X-101 — Release engineering across repositories
- **Size:** L · **Depends on:** CORE-125, DESK-101, WEB-101, SRV-001 · **Decisions:** ADR-0026, ADR-0017, ADR-0002
- **Attach:** all five repositories
- **Scope:** versioning and changelogs; tagged core releases producing the C SDK, WebAssembly package (npm, trusted publishing) and CLI; SBOMs (CycloneDX) and provenance attestations for every artifact; immutable releases; container signing (keyless Sigstore); signing pipelines for desktop (with the owner's accounts); reproducible-build checks; release checklists including fidelity scores and the parity test.

### X-102 — Nightly cross-repository integration
- **Size:** M · **Depends on:** CORE-125, DESK-101, WEB-101
- **Attach:** all code repositories
- **Scope:** nightly workflows that build desktop and web against core `main` and run their end-to-end suites; failure notifications to the owner; a compatibility matrix of core versions versus shell versions.
