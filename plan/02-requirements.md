# 02 — Requirements

Every requirement has a stable ID so that work packages, tests and reviews can trace back to it. Priorities use MoSCoW (**M**ust, **S**hould, **C**ould). "Phase" is the roadmap phase in which the requirement is first met (see [04-roadmap.md](04-roadmap.md)); later phases may deepen it. Verification names how we prove it.

Phases: P0 Foundations · P1 Faithful Viewer · P2 Writer · P3 Together · P4 Press · P5 Insight · P6 1.0 Parity+.

## FID — Fidelity and compatibility

| ID | Requirement | Pri | Phase | Verification |
|---|---|---|---|---|
| FID-01 | Import `.docx`, `.dotx`, `.docm`, `.dotm` natively in Rust: ECMA-376 Transitional and Strict, plus Microsoft extensions documented in [MS-DOCX]. | M | P1 | Corpus import with zero crashes; coverage matrix |
| FID-02 | Tier A determinism: identical layout and reference-raster output on all supported platforms for a given version. | M | P0 proven, P1 enforced | Determinism CI matrix |
| FID-03 | Tier B lossless round-trip: untouched content survives open/save unchanged; untouched parts byte-identical. | M | P1 | Round-trip suite, fuzzing, Word re-open check in lab |
| FID-04 | Tier C measured fidelity with scores published per release; targets per phase. | M | P1 | Fidelity Lab report |
| FID-05 | Tier D: BayanDocs-authored documents lay out identically in Word (fonts embedded when needed, conservative OOXML). | M | P2 | Lab: author in BayanDocs, measure in Word |
| FID-06 | Honor Word compatibility modes (`compatibilityMode` 11/12/14/15) and every compatibility setting that affects layout. | M | P1→P4 | Lab studies per mode |
| FID-07 | Font resolution per ADR-0010 with a visible font-availability status for each document. | M | P1 | Unit + UI tests |
| FID-08 | Fidelity Inspector: list features and fonts in the open document that BayanDocs does not reproduce exactly. | S | P2 | UI test against tagged corpus |
| FID-09 | Never convert a document to a newer compatibility mode without explicit user action. | M | P2 | Round-trip tests |
| FID-10 | Open and save password-encrypted Word files (MS-OFFCRYPTO Agile Encryption). | M | P2 | Interop tests with Word-encrypted samples |

## FMT — File formats

| ID | Requirement | Pri | Phase | Verification |
|---|---|---|---|---|
| FMT-01 | Read and write `.docx` family; write edits with minimal changes to the original XML. | M | P1 read, P2 write | Round-trip + lab |
| FMT-02 | Read and write RTF, including as the rich-text clipboard format on Windows and macOS. | M | P2 | Clipboard interop tests with Word, LibreOffice, browsers |
| FMT-03 | Import legacy `.doc` (Word 97–2003, MS-DOC). Export is a later "could". | M | P4 | Corpus import |
| FMT-04 | Import and export OpenDocument Text (`.odt`). | S | P4 | Round-trip with LibreOffice |
| FMT-05 | PDF export: basic (P1); PDF/A-2b/3b/4 and PDF/UA (P2–P4); PDF/X-4 and X-1a (P4). | M | P1→P4 | veraPDF and preflight validation in CI |
| FMT-06 | HTML import (paste) and export. | M paste / S export | P2 / P4 | Paste interop tests |
| FMT-07 | Markdown import and export. | S | P2 / P4 | Unit tests |
| FMT-08 | Plain text import and export with encoding detection. | M | P2 | Unit tests |
| FMT-09 | EPUB 3 export. | C | P5 | epubcheck |
| FMT-10 | Images: render PNG, JPEG, GIF, BMP, TIFF, WebP, SVG, EMF, WMF, EMF+; insert them. | M | P1 render / P2 insert | Image corpus |
| FMT-11 | Preserve unknown parts and extensions, VBA projects, custom XML parts and signatures. | M | P1 | Round-trip suite |
| FMT-12 | Open PDFs for reflow editing. | C | P6 | — |

## ARC — Architecture

| ID | Requirement | Pri | Phase | Verification |
|---|---|---|---|---|
| ARC-01 | All document logic (model, formats, layout, rendering, editing, proofing, sync, crypto) lives in the Rust core. | M | P0+ | Architecture review |
| ARC-02 | The core builds as native libraries (Windows, macOS, Linux; x86-64 and arm64) and as wasm32. | M | P0 | CI matrix |
| ARC-03 | Shells are thin; desktop and web feature parity is guaranteed by the shared UI manifest. | M | P2 | Parity test listing commands per shell |
| ARC-04 | The desktop app works fully offline with no network dependency. | M | P1 | Offline CI job |
| ARC-05 | The web app works offline after first load (installable PWA) for local files. | S | P1/P2 | Playwright offline test |
| ARC-06 | The self-hosted server runs as one container with no required external services. | M | P3 | `docker run` smoke test |
| ARC-07 | The engine boundary is a versioned message protocol; sessions can be recorded and replayed on any platform. | M | P0/P1 | Replay test in CI |
| ARC-08 | The core never opens network sockets; hosts provide transport. | M | P0 | Dependency/API audit |

## EDT — Editing features (Word parity)

The detailed, element-level checklist is [specs/coverage-matrix.md](../specs/coverage-matrix.md). This table fixes the phase in which each feature family must be usable.

| ID | Feature family | Pri | Phase |
|---|---|---|---|
| EDT-01 | Character and paragraph formatting (all `w:rPr` / `w:pPr` properties), format painter, clear and reveal formatting, change case, drop caps | M | P2 |
| EDT-02 | Styles: apply, create, modify with impact preview, style inspector, organizer; themes; no silent auto-redefinition | M | P2 |
| EDT-03 | Lists: bullets, numbering, multilevel, list styles, restart/continue, heading outline numbering (legal documents) | M | P2 |
| EDT-04 | Page setup, sections, columns, headers and footers, page numbers, line numbers, page borders, watermarks, page color | M | P2 |
| EDT-05 | Tables: insert, draw, structure editing, merge/split, styles, autofit, sort, formulas, text↔table conversion, header-row repeat | M | P2 |
| EDT-06 | Pictures (crop, wrap, position, basic effects), shapes, text boxes, WordArt | M | P2 |
| EDT-07 | Hyperlinks, bookmarks, cross-references, captions | M | P2 |
| EDT-08 | Fields: full parsing; evaluation of all common field types; update and lock; field-code view | M | P2 (common) → P4 (all) |
| EDT-09 | Footnotes and endnotes | M | P2 |
| EDT-10 | Track changes (all revision types, accept/reject, display modes, lock tracking) and threaded comments | M | P2 |
| EDT-11 | Find and replace with formatting, special characters and Word-style wildcards; Go To; select similar | M | P2 |
| EDT-12 | AutoCorrect, AutoFormat-as-you-type (including Markdown-style shortcuts), building blocks / Quick Parts | M | P2 |
| EDT-13 | Clipboard: paste options (keep source, merge, text only), interop with Word, LibreOffice, Google Docs, browsers, email clients | M | P2 |
| EDT-14 | Undo/redo with history, repeat last action | M | P2 |
| EDT-15 | Tables of contents, table of figures, citations and bibliography, indexes, table of authorities | M | P4 (TOC in P2) |
| EDT-16 | Equations (OMML) display (P1) and editing (P4) | M | P1 / P4 |
| EDT-17 | Charts display (P1) and editing with embedded data (P4); SmartArt display (P1) and editing (P5) | M | P1 / P4–P5 |
| EDT-18 | Content controls (all types), legacy form fields, XML data binding, protection for forms | M | P4 |
| EDT-19 | Compare and combine documents (legal blackline) | M | P4 |
| EDT-20 | Restrict editing, mark as final, document inspector (remove hidden metadata) | M | P4 |
| EDT-21 | Digital signatures: preserve (P1), verify (P4), create (P4) | M | P1 / P4 |
| EDT-22 | Mail merge (CSV, XLSX, ODS, JSON sources), envelopes and labels | M | P4 |
| EDT-23 | Views: print layout, web layout, draft, outline, read mode, focus; navigation pane with heading drag-reorder; split window; side-by-side | M | P2 (outline P4) |
| EDT-24 | Templates (`.dotx`/`.dotm`), a default "Normal" template, document properties | M | P2 |
| EDT-25 | Word count, document statistics, language marking | M | P2 |

## COL — Collaboration and data sovereignty

| ID | Requirement | Pri | Phase | Verification |
|---|---|---|---|---|
| COL-01 | Real-time co-authoring on CRDTs: no locks, guaranteed convergence. | M | P3 | Randomized multi-client convergence tests |
| COL-02 | Presence: remote cursors, selections, names, colors. | M | P3 | E2E tests |
| COL-03 | Offline editing with automatic merge on reconnect, never overwriting others' work. | M | P3 | Partition tests |
| COL-04 | Zero-knowledge E2EE of content, titles, comments, media, history and folder structure. | M | P3 | Protocol review, external audit |
| COL-05 | Sharing with roles (owner, editor, commenter, viewer), E2EE link sharing, revocation. | M | P3 | Authorization test matrix |
| COL-06 | Multiple devices per user with cross-signed device keys and account recovery. | M | P3 | Security review |
| COL-07 | Version history: named versions, restore, compare any two versions. | M | P3 | E2E tests |
| COL-08 | Comments and suggestions (tracked changes) in real time. | M | P3 | E2E tests |
| COL-09 | Enterprise identity: OIDC single sign-on (P3), SCIM provisioning (P4), compliance escrow member (P4). | M/S | P3–P4 | Interop with Keycloak, Authentik, Entra ID |
| COL-10 | Notifications that leak no document content. | S | P3 | Review |
| COL-11 | Federation between independently hosted servers. | C | P6+ | Research |
| COL-12 | Merge two BayanDocs-edited copies of the same `.docx` exchanged as files, using embedded history. | C | P5 | Tests |

## SEC — Security and privacy

| ID | Requirement | Pri | Phase | Verification |
|---|---|---|---|---|
| SEC-01 | All untrusted input is parsed by memory-safe code. | M | P0+ | Dependency audit |
| SEC-02 | No external content is fetched or executed automatically (linked images, remote templates, INCLUDE fields, DDE, OLE activation, remote fonts); explicit per-document consent. | M | P1 | Malicious-sample suite |
| SEC-03 | Macros never auto-run; any execution is sandboxed and capability-limited. | M | P4/P5 | Sandbox tests |
| SEC-04 | No telemetry by default; crash reports opt-in and free of content. | M | P1 | Network-traffic test |
| SEC-05 | Supply-chain policy (ADR-0017) enforced in CI. | M | P0 | CI gates |
| SEC-06 | Signed releases, SBOMs and build provenance attestations. | M | P1 | Release checklist |
| SEC-07 | All parsers fuzzed in CI and continuously. | M | P1 | Fuzz dashboards |
| SEC-08 | External security audit of E2EE and server before collaboration GA; full audit before 1.0. | M | P3 / P6 | Audit reports |
| SEC-09 | Published vulnerability disclosure policy with private reporting. | M | P0 | `SECURITY.md` |
| SEC-10 | Web hardening: strict CSP, Trusted Types, cross-origin isolation, Subresource Integrity, no third-party runtime origins. | M | P1 | Header tests |
| SEC-11 | Locally cached collaborative documents encrypted at rest with OS-keychain-protected keys. | S | P3 | Review |
| SEC-12 | Threat model maintained per component ([specs/threat-model.md](../specs/threat-model.md)). | M | P0+ | Phase-gate review |

## TYP / PUB — Typography, publishing and print

| ID | Requirement | Pri | Phase | Verification |
|---|---|---|---|---|
| TYP-01 | OpenType shaping for all scripts; kerning, ligatures, true small caps (synthesized fallback as Word does), number forms and spacing, stylistic sets, contextual alternates. | M | P1 render / P4 UI | Lab + unit tests |
| TYP-02 | Word-faithful defaults: features applied exactly when and how Word applies them. | M | P1 | Lab |
| TYP-03 | Optional enhanced typography for BayanDocs-native documents (optimal line breaking, hanging punctuation, optical margins), stored as ignorable extensions with a Word-compatibility warning. | C | P5 | Unit tests |
| TYP-04 | Automatic and manual hyphenation per language. | M | P2 | Lab |
| PUB-01 | PDF export with subset-embedded fonts, links, outline, metadata. | M | P1 | veraPDF syntax checks |
| PUB-02 | PDF/A archival output (2b, 3b, 4), validated in CI. | M | P2–P4 | veraPDF |
| PUB-03 | PDF/UA tagged output, validated in CI. | M | P2–P4 | veraPDF PDF/UA |
| PUB-04 | PDF/X-4 and X-1a with ICC output intents; ICC-based CMYK conversion with rendering intents; rich black, overprint, spot colors. | M | P4 | Preflight validation |
| PUB-05 | Bleed and slug, trim box, crop and registration marks, stored as Word-ignorable extensions. | M | P4 | Unit + visual tests |
| PUB-06 | Print preview and printing with exact layout on all desktop platforms; web printing via generated PDF. | M | P1 | Print tests |
| PUB-07 | Color management of images with embedded ICC profiles. | S | P4 | Unit tests |

## UI — Interface and experience

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| UI-01 | Classic mode: ribbon with a Word-familiar structure, Quick Access Toolbar, KeyTips, Word-compatible shortcuts on each platform. | M | P2 |
| UI-02 | Ribbon and shortcut customization, with import/export of customizations. | S | P4 |
| UI-03 | Focus mode: interface hidden until text is selected, floating selection toolbar, Markdown-style shortcuts, typewriter scrolling, optional reflowed (non-paginated) view. | M | P2 |
| UI-04 | Panes: navigation, styles, comments, revisions, find, selection, thesaurus. | M | P2 |
| UI-05 | Dialogs defined declaratively in the shared UI manifest and rendered by each shell. | M | P2 |
| UI-06 | Light, dark and high-contrast themes; dark document canvas as a display transform that never changes the document. | M | P2 |
| UI-07 | Context menus and a mini toolbar. | M | P2 |
| UI-08 | Touch and pen on tablets and convertibles. | S | P4 |
| UI-09 | A distinct visual identity: familiar structure, no Microsoft trademarks or trade dress. | M | P2 |

## A11Y — Accessibility

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| A11Y-01 | Interfaces conform to WCAG 2.2 AA and EN 301 549; VPAT published. | M | P2 baseline, P6 certified |
| A11Y-02 | Screen readers can read (P1) and edit (P2) documents: NVDA, JAWS, Narrator, VoiceOver, Orca. | M | P1 / P2 |
| A11Y-03 | Every feature operable by keyboard alone. | M | P2 |
| A11Y-04 | Document accessibility checker (alt text, heading structure, table headers, contrast, reading order). | M | P4 |
| A11Y-05 | Tagged PDF/UA export. | M | P2–P4 |
| A11Y-06 | High contrast, interface scaling to 200%+, reduced motion. | M | P2 |
| A11Y-07 | Read aloud (local text-to-speech) and dictation (local speech-to-text). | S | P5 |

## I18N — Internationalization

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| I18N-01 | Full Unicode with complex-script shaping (Arabic, Hebrew, Indic, Thai, Khmer, …). | M | P1 |
| I18N-02 | Bidirectional text; right-to-left paragraphs, sections and tables, exactly as Word lays them out. | M | P1 / P2 |
| I18N-03 | Arabic kashida justification as Word applies it. | M | P2 |
| I18N-04 | East Asian layout: line-breaking rules (kinsoku), character grid, auto-spacing between Asian and Latin text (P2); ruby, combined characters, two-lines-in-one, vertical text (P4). | M | P2 / P4 |
| I18N-05 | Interface localization via Project Fluent; pseudo-locale testing; mirrored right-to-left interface. | M | P2 |
| I18N-06 | Locale-aware fields and numbering: dates in Gregorian, Hijri, Hebrew, Japanese era and Thai calendars; ordinal and cardinal number text. | M | P2 / P4 |
| I18N-07 | Input methods (CJK, Indic, Vietnamese, …), dead keys and emoji pickers on every platform. | M | P2 |

## PRF — Proofing and language tools

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| PRF-01 | Spell checking with Hunspell-compatible dictionaries, following each run's language tag. | M | P2 |
| PRF-02 | Grammar and style checking: a deterministic rules engine for English first; deeper checks via local AI; other languages via plugins. | S | P2 / P5 |
| PRF-03 | Thesaurus from openly licensed data. | C | P4 |
| PRF-04 | Custom dictionaries, ignore lists, per-document proofing state. | M | P2 |
| PRF-05 | Automatic language detection. | S | P4 |

## AI — Local intelligence

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| AI-01 | AI features run on the user's device by default. Content leaves the device only if the user or their administrator configures an inference endpoint they control, and the interface says so whenever that is the case. | M | P5 |
| AI-02 | Suggestions are non-destructive annotations, never applied without the user's action. | M | P5 |
| AI-03 | Models under OSI-approved licenses, downloaded on demand and integrity-verified. | M | P5 |
| AI-04 | Hardware-adaptive (CPU, GPU, NPU where available) with graceful degradation. | S | P5 |
| AI-05 | Administrators can disable AI entirely by policy. | M | P5 |

## AUT — Automation and macros

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| AUT-01 | Preserve VBA projects in `.docm`/`.dotm` untouched. | M | P1 |
| AUT-02 | Read-only viewer for VBA source. | S | P4 |
| AUT-03 | Sandboxed JavaScript/TypeScript automation API with capability prompts. | M | P5 |
| AUT-04 | Assisted VBA → JavaScript translation (rules plus local AI) with a review interface. | S | P5 |
| AUT-05 | Opt-in, sandboxed compatibility runtime for a documented subset of the Word object model. | C | P6 |
| AUT-06 | Extensions as sandboxed WebAssembly components that run identically on desktop and web. | S | P5 |

## PERF — Performance and resources

Reference hardware: a 2020-era mid-range laptop (4-core x86-64 or Apple M1, 8 GB RAM, SSD) and a current evergreen browser on it. "Typical document": 50 pages of mixed text, tables and images.

| ID | Budget | Pri | Phase |
|---|---|---|---|
| PERF-01 | Desktop cold start to interactive window ≤ 1.0 s; warm start ≤ 0.4 s. | M | P2 |
| PERF-02 | Open a typical document: first page visible ≤ 300 ms (desktop) / ≤ 800 ms (web, app already loaded); full layout ≤ 1 s. | M | P1 |
| PERF-03 | 1,000-page document: first page ≤ 1 s; complete background layout ≤ 10 s; editing stays responsive throughout. | M | P1 / P2 |
| PERF-04 | Keystroke-to-pixel latency p95 ≤ 16 ms and p99 ≤ 33 ms, for documents up to 1,000 pages. | M | P2 |
| PERF-05 | Desktop memory ≤ 150 MB for a typical document, ≤ 500 MB for 1,000 pages (excluding memory-mapped fonts). | M | P2 |
| PERF-06 | Web initial download ≤ 5 MB compressed excluding fonts; time to interactive ≤ 2.5 s on broadband. | M | P1 |
| PERF-07 | A remote edit appears on collaborators' screens ≤ 250 ms p95 within one region. A 2 vCPU / 4 GB server instance supports ≥ 1,000 concurrently active documents and ≥ 5,000 connected clients. | M | P3 |
| PERF-08 | Budgets are enforced by CI benchmarks; regressions above 5% block merging unless explicitly accepted. | M | P1 |

## REL — Reliability and data safety

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| REL-01 | Auto-recovery journal: at most 2 seconds of work lost on a crash or power loss. | M | P2 |
| REL-02 | Atomic saves (write, flush, rename); the original file is never truncated by a failed save. | M | P2 |
| REL-03 | Best-effort repair of damaged files, with a report of what was recovered. | S | P4 |
| REL-04 | Server backup and restore tooling, tested. | M | P3 |
| REL-05 | Huge or malicious files are handled within resource limits, with cancellation and clear errors. | M | P1 |

## OPS — Operations and self-hosting

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| OPS-01 | One-command deployment (`docker run`) with safe defaults; HTTPS via reverse proxy or built-in ACME. | M | P3 |
| OPS-02 | Configuration via environment and file; secrets via files; twelve-factor friendly. | M | P3 |
| OPS-03 | Metrics (Prometheus / OpenTelemetry) and structured logs without content. | M | P3 |
| OPS-04 | Upgrades apply database migrations automatically, with documented rollback. | M | P3 |
| OPS-05 | Scale-out mode: PostgreSQL, S3-compatible storage, multiple instances. | S | P4 |
| OPS-06 | Admin console and CLI: users, storage, quotas, policies. | M | P3 |
| OPS-07 | Air-gapped deployments: fonts, dictionaries and AI models served locally. | M | P3 / P5 |

## PLT — Supported platforms

| ID | Requirement | Pri | Phase |
|---|---|---|---|
| PLT-01 | Desktop: Windows 11 and Windows 10 22H2 (best effort after Microsoft's end of support), x86-64 and arm64; macOS current and two previous major versions on Apple silicon (Intel while Apple and Qt support it); Linux x86-64 and arm64 via Flatpak, AppImage, `.deb` and `.rpm`. | M | P1 |
| PLT-02 | Browsers: last two major versions of Chrome, Edge, Firefox and Safari on desktop; tablets for viewing (P1) and editing (P4). | M | P1 / P4 |
| PLT-03 | Server: Linux containers on x86-64 and arm64. | M | P3 |
