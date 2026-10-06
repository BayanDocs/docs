# 07 — Quality, Security and Testing

Quality in BayanDocs is enforced by machines, not by memory. Every promise in the [Fidelity Contract](01-vision-and-fidelity-contract.md#the-fidelity-contract) and every budget in the [requirements](02-requirements.md) maps to an automated check. The governing decisions are ADR-0025 (quality gates), ADR-0017 (supply chain) and ADR-0023 (active content).

## 1. Testing strategy by repository

### bayan-core

| Kind | Purpose | Tooling (decided in CORE-001 / later WPs) |
|---|---|---|
| Unit tests | Every module's behavior | `cargo test` |
| Property-based tests | Model invariants, CRDT convergence (random concurrent edits on several replicas must converge to the same valid document), unit conversions, round-trip of generated documents | `proptest` |
| Snapshot tests | Layout trees and imported models serialized as JSON, reviewed when they change | `insta` |
| Golden raster tests | Pixel hashes of rendered pages for a fixed set of documents | in-house harness |
| Determinism matrix | The same documents must produce identical layout and pixel hashes on Linux x86-64, Windows x86-64, macOS arm64 and wasm32 (Node and a headless browser) | CI matrix + hash comparison job |
| Fidelity Lab | Agreement with Microsoft Word (see [specs/fidelity-lab.md](../specs/fidelity-lab.md)) | `lab/` tools |
| Round-trip tests | Open → save → open is content-identical; untouched parts byte-identical | corpus-driven harness |
| Fuzzing | Every parser (ZIP, XML, DOCX parts, RTF, DOC, ODT, fonts, images, EMF/WMF, SVG, field codes, engine protocol messages) | `cargo-fuzz` in CI (short runs) plus continuous runs (ClusterFuzzLite, then OSS-Fuzz when eligible) |
| WebAssembly tests | The same unit tests compiled to wasm32 | `wasm-bindgen-test` |
| Benchmarks | Performance budgets; regressions above 5% fail | benchmark harness with stored baselines |
| Memory checks | Memory budgets for reference documents | heap profiling in benchmark jobs |
| Miri | Undefined-behavior checks for crates that contain `unsafe` (FFI) | `cargo miri test` |

### bayan-desktop

Unit and integration tests with Qt Test against a mock engine and the real engine library; screenshot tests of the interface chrome (the document canvas is engine-rendered and already covered by core); accessibility-tree assertions through `QAccessible`; AddressSanitizer and UndefinedBehaviorSanitizer builds on Linux; `clang-tidy` and `clang-format` checks; packaging smoke tests (install, launch, open a document, quit) on each OS.

### bayan-web

Vitest unit tests; Playwright end-to-end tests in Chromium, Firefox and WebKit; automated accessibility rules (axe) on every page and dialog; offline tests for the PWA; security-header tests (CSP, Trusted Types, cross-origin isolation); IME composition tests through Chromium's DevTools protocol; bundle-size budgets.

### bayan-server

Unit tests; integration tests against SQLite and PostgreSQL; protocol tests with the reference sync client; an authorization matrix (every role × every action, including forged and replayed messages); fuzzing of every message decoder; load tests for PERF-07; partition and reconnect tests; database migration tests (upgrade and rollback); backup-and-restore tests; container image vulnerability scanning.

### Cross-repository

A nightly integration workflow builds the desktop and web shells against the latest core and runs their end-to-end suites. From Phase 3, a collaboration suite runs two web clients, one desktop client and a server in containers, applies scripted concurrent edits including network partitions, and asserts that every client converges to identical content and identical layout hashes.

### Accessibility and internationalization testing

- Automated rules (axe for web, accessibility-tree assertions for desktop) on every pull request.
- Scripted manual screen-reader passes before each release (NVDA and JAWS on Windows, VoiceOver on macOS and iOS, Orca on Linux, TalkBack on Android for the web viewer).
- Testing with disabled users before Phase 2 beta and every major release; the owner recruits testers (see [09-owner-checklist.md](09-owner-checklist.md)).
- Pseudo-localization (accented, 40% longer strings, right-to-left pseudo-locale) on every pull request that touches the interface.
- An internationalization corpus in the lab: Arabic, Hebrew, Persian, Urdu, Chinese (simplified and traditional), Japanese, Korean, Hindi, Bengali, Tamil, Thai, Khmer, Vietnamese and mixed-direction documents.
- An input-method test matrix (Microsoft IME, macOS input sources, IBus and Fcitx on Linux, Gboard and iOS keyboards in browsers).

## 2. CI gates per repository

| Repo | Gate on every pull request | Nightly / scheduled |
|---|---|---|
| core | format, lint (warnings are errors), tests (native and wasm32), supply-chain checks, documentation build, fuzz smoke runs, determinism subset, fidelity subset (once the engine renders documents) | full determinism matrix, full public-corpus fidelity, benchmarks, long fuzzing |
| desktop | build and test on Windows, macOS, Linux; format and lint; sanitizer build; supply-chain checks | packaging and signing dry run, integration against latest core |
| web | frozen-lockfile install with scripts disabled, lint and format, type check, unit tests, end-to-end tests in three engines, accessibility rules, bundle budget, audit and lockfile integrity | integration against latest core |
| server | as core, plus integration tests on SQLite and PostgreSQL, container build and scan | load tests, migration tests |
| docs | site build, link check, spell check | — |
| all | workflow security lint, secret scanning with push protection | OpenSSF Scorecard |

No gate may be weakened to make a change pass (see [AGENTS.md §4](../AGENTS.md#4-the-verification-gate-is-sacred)).

## 3. Security program

### Secure development lifecycle

1. **Threat models** per component ([specs/threat-model.md](../specs/threat-model.md)), updated at each phase gate and whenever a work package changes a trust boundary.
2. **Security-sensitive paths** (parsers, cryptography, authentication, authorization, the FFI boundary, update mechanisms, and the CI workflows and the checks they run in `.github/`) are listed in each repository's `CODEOWNERS`; changes to them require a dedicated security review session in addition to the normal review. `.github/` is on the list because a workflow triggered by a pull request runs that pull request's own copy of it, so a change there can weaken the checks that judge it.
3. **Static analysis:** strict lints, CodeQL for C++, TypeScript and workflows, a workflow security linter, `clang-tidy`.
4. **Dynamic analysis:** fuzzing, sanitizers, Miri.
5. **Dependencies:** ADR-0017 in full.
6. **External audits:** the cryptographic design and server before collaboration GA (Phase 3); a full audit before 1.0. Funding programmes for open source (see the owner checklist) sometimes include audits.

### Document-borne threats we refuse to replicate

Word has a long history of attacks delivered through documents. BayanDocs blocks each of these by default and requires explicit, per-document user consent for the few that have legitimate uses (ADR-0023):

| Vector | BayanDocs behavior |
|---|---|
| VBA macros, including auto-run macros | Preserved untouched; never executed automatically; execution (later phases) only in a sandbox |
| DDE / DDEAUTO fields | Never executed; displayed as their cached result with a warning |
| Remote template injection (`attachedTemplate` pointing to http or UNC paths) | Never fetched |
| External relationships (`TargetMode="External"`) for images, frames, subdocuments, OLE | Never fetched automatically; placeholder plus consent bar |
| `INCLUDETEXT`, `INCLUDEPICTURE`, `LINK` fields | Cached result shown; never refreshed without consent |
| OLE objects and ActiveX controls | Preview image shown; never activated |
| Hyperlinks to dangerous protocol handlers (`ms-msdt:`, `search-ms:`, `file:` and others) | Blocked or confirmed with an explicit warning |
| UNC paths that leak Windows credentials | Never resolved automatically |
| XML external entities and entity expansion | Document type definitions are rejected outright |
| ZIP bombs and path traversal | Hard limits on entry count, sizes, compression ratio; part names are validated |
| Decompression bombs in images | Dimension and memory limits before decoding |
| Malformed fonts, images, EMF/WMF, SVG | Parsed only by memory-safe code; fuzzed; SVG scripts and external references ignored |

### Release integrity

Signed releases on every platform, a software bill of materials for every release artifact, build provenance attestations, checksums, and a signed update channel (ADR-0026). Reproducible builds are a goal from Phase 1 and a requirement by 1.0.

### Vulnerability management

`SECURITY.md` in every repository, GitHub private vulnerability reporting enabled, advisories and CVE identifiers issued through GitHub Security Advisories, and target response times: acknowledge within 3 days; fix critical issues within 7 days and high within 30 days of confirmation (subject to the 24-hour dependency rule, with mitigations in the meantime).

### Privacy

No telemetry. Crash reports are opt-in, created locally, shown to the user before sending, and contain no document content. The server stores the minimum metadata required to route ciphertext, and the threat model documents exactly what that metadata reveals (who collaborates with whom, when, and how much).

## 4. Performance engineering

- Budgets from [02-requirements.md](02-requirements.md#perf--performance-and-resources) are encoded as benchmark thresholds.
- A reference document set (typical 50-page, 1,000-page book, table-heavy report, image-heavy brochure, mixed-script document) is used for all benchmarks.
- Keystroke-to-pixel latency is measured end to end in both shells with automated input injection.
- Incremental layout is mandatory from the first layout work package; full re-layout on every edit is never acceptable even as a temporary measure in shipped code.
