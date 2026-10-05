# Phase 1 — Faithful Viewer: cross-repository work packages (drafts)

**Status: Draft**, refined at the Phase-0 gate.

### X-101 — Release engineering across repositories
- **Size:** L · **Depends on:** CORE-125, DESK-101, WEB-101, SRV-001 · **Decisions:** ADR-0026, ADR-0017, ADR-0002
- **Attach:** all five repositories
- **Scope:** versioning and changelogs; tagged core releases producing the C SDK, WebAssembly package (npm, trusted publishing) and CLI; SBOMs (CycloneDX) and provenance attestations for every artifact; immutable releases; container signing (keyless Sigstore); signing pipelines for desktop (with the owner's accounts); reproducible-build checks; release checklists including fidelity scores and the parity test.
- **Third-party notices in distributed artifacts** (recorded in the review of [BayanDocs/bayan-server#1](https://github.com/BayanDocs/bayan-server/pull/1), SRV-001): the server's container image, built `FROM scratch`, holds a statically linked binary that contains code from our crates' dependencies, Rust's standard library, musl and LLVM's libunwind, but none of their license texts. Several of these licenses, MIT among them, require their copyright and license notices to accompany every copy, so the image must carry them before it is published. Generate the notices from what is compiled into the binary with a pinned tool (for example `cargo about`, added under ADR-0017), ship them in the image, and add the file to the image's file list in bayan-server's `scripts/container-smoke-test.sh`. Check the same for the core release artifacts (C SDK, CLI, WebAssembly package); bayan-web already publishes its notices, and DESK-104 ships the desktop's Qt notices.

### X-102 — Nightly cross-repository integration
- **Size:** M · **Depends on:** CORE-125, DESK-101, WEB-101
- **Attach:** all code repositories
- **Scope:** nightly workflows that build desktop and web against core `main` and run their end-to-end suites; failure notifications to the owner; a compatibility matrix of core versions versus shell versions.
