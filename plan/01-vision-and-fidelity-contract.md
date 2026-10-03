# 01 — Vision, Principles and the Fidelity Contract

## Vision

BayanDocs is a word processor that a Microsoft Word user can switch to without giving anything up, and that gives them what Word cannot: the same layout on every device, editing that works fully offline, collaboration whose server cannot read the documents, AI assistance that never leaves the machine, and a codebase anyone can read, audit, run and improve.

It is one product with two faces, a native desktop application and a browser application, sharing a single engine. It is free and open source in its entirety, with no paid tier holding back features.

## Product principles

These principles are ordered. When two of them conflict, the higher one wins. Every agent and reviewer uses them to break ties.

1. **Never lose, corrupt, or silently alter user content.** Round-trip safety beats features. A feature that risks data loss does not ship.
2. **Secure and private by default.** No telemetry, no automatic external fetches, macros off, encryption on, memory-safe parsing.
3. **The layout is the layout.** A document lays out identically on every platform BayanDocs runs on.
4. **Measured Word fidelity.** We publish numbers, not adjectives. Every release reports how closely it matches Microsoft Word on a public corpus.
5. **Fast and light.** Performance budgets are requirements, enforced in CI, not aspirations.
6. **Everyone can use it.** Accessibility, right-to-left scripts, East Asian typography and localization are release gates, not add-ons.
7. **Sovereign and simple to operate.** Local-first by default; one container to self-host; no dependency on any vendor's cloud.
8. **Open all the way down.** Open source code, open file formats, openly documented Word behaviors, no open-core split.

## How this plan reads the specification

The founding specification is ambitious and mostly right. Where it is ambiguous or technically imprecise, this plan sharpens it. Nothing here lowers the ambition; it makes the ambition testable.

| Specification item | How the plan interprets it | Where |
|---|---|---|
| "Pixel-perfect binary rendering … parsing of the OpenXML (.docx) specification down to the binary level" | A `.docx` file is a ZIP package of XML parts (Office Open XML, ECMA-376 / ISO/IEC 29500), not a binary format. The binary format is legacy `.doc` (MS-DOC), which we also import. All parsing is native Rust in our own engine, with no conversion through third-party tools. | ADR-0007, ADR-0018 |
| "Layouts must never shift a single pixel" | Split into the four-tier Fidelity Contract below. An absolute guarantee is achievable and enforced between BayanDocs installations. Against Microsoft Word it is a measured, published, continuously rising target, because Word's layout algorithm is unpublished and Word itself lays out differently across its own versions and platforms. | This file, ADR-0004 |
| "Zero layout modification … never flow onto a new page unpredictably" | Lossless round-trip (Tier B) plus measured fidelity (Tier C). We also read Word's own `w:lastRenderedPageBreak` hints to detect where our pagination disagrees with the last Word that saved the file. | ADR-0004, specs/fidelity-lab.md |
| "Bespoke font mapping engine" | A bundled library of metric-compatible open fonts, support for fonts embedded in documents, an organization font library on the server, and a gap programme for Microsoft fonts that have no open equivalent. Aptos, Word's default font since 2023–2024, is the single largest fidelity risk. | ADR-0010, specs/font-compatibility.md |
| "Run legacy VBA macros, or instantly translate them" | Staged: preserve macros untouched → let users inspect them → assisted translation to modern JavaScript with human review → a sandboxed compatibility runtime for a documented subset of Word's object model. Macros never run automatically. Complete, instant translation of arbitrary VBA is not achievable by anyone; we commit to measured coverage instead. | ADR-0023 |
| "Shared Rust/WebAssembly core" | Yes, and further: not only rendering but the document model, import/export, editing logic, proofing, collaboration and encryption live in the core, so the desktop and web shells stay thin and cannot drift apart. | ADR-0006, ADR-0012 |
| "Native desktop shell in C++/Qt" | Yes. Qt 6 with Qt Quick for the interface; C++ only as glue. Speed comes mainly from the Rust core. | ADR-0013 |
| "Sovereign web shell … simple Docker container" | Yes. One container with an embedded database and local disk storage by default; PostgreSQL and S3-compatible storage optional. | ADR-0015 |
| "Real-time co-authoring (CRDTs)" | Yes, on a document model shaped like Word's own internal model so that concurrent edits merge the way a Word user expects. | ADR-0007, ADR-0008 |
| "Zero-knowledge E2EE" | Yes, using the IETF Messaging Layer Security standard (RFC 9420). We are explicit about what a server that cannot read documents cannot do (server-side search, previews, content in notification emails) and how each is replaced on the client. | ADR-0016 |
| "Local-first offline sync" | Yes. Local-first is the default architecture even for a single user with no server. | ADR-0008 |
| "Advanced typography matrix" | Yes. In addition, we reproduce Word's own typographic choices exactly (for example, Word applies kerning only when the document enables it), so "better typography" never silently changes a Word document. Enhanced typography such as optimal paragraph line breaking is opt-in per document. | ADR-0009 |
| "Strict section and style isolation" | Style changes are explicit operations with an impact preview ("this changes 340 paragraphs on 52 pages"), no hidden automatic style redefinition, deterministic paste-conflict handling, and numbering that cannot bleed between lists. | plan/02-requirements.md |
| "Enterprise print engine … PDF/A for commercial print houses" | PDF/A is the archival standard; print houses expect PDF/X. We deliver PDF/X-4 (and X-1a), PDF/A, and PDF/UA (accessible PDF), with ICC-based CMYK conversion. Bleed and slug are not Word concepts, so they are stored as BayanDocs extensions that Word safely ignores. | ADR-0011, ADR-0018 |
| "Classic mode ribbon / Focus mode" | Yes, plus Word-compatible keyboard shortcuts and KeyTips (the Alt-key sequences power users rely on). Both modes are generated from one shared UI definition so desktop and web stay identical. | ADR-0019 |
| "Privacy-first local AI" | Yes. Off by default until the user enables it, local-only by default, using models under OSI-approved licenses. Organizations may point it at an inference server they control; it is never sent to BayanDocs project servers. | ADR-0024 |

## What "as good as Word in every way" also requires

The specification does not list these, but a Word user would notice their absence on day one. They are in the requirements and the roadmap.

- **Accessibility:** screen readers on every platform, full keyboard operation, an accessibility checker, tagged accessible PDF export, high-contrast themes.
- **Internationalization:** right-to-left scripts (Arabic, Hebrew, Persian, Urdu) including kashida justification, East Asian typography (line-breaking rules, character grid, ruby, vertical text), Indic and Southeast Asian scripts, input methods, a translated interface.
- **Proofing:** spelling, grammar, hyphenation, thesaurus, per-language dictionaries.
- **Formats:** legacy `.doc`, `.rtf` (also how rich text moves through the system clipboard), `.odt`, templates (`.dotx`/`.dotm`), HTML and Markdown, EPUB, password-encrypted Word files.
- **References:** tables of contents, footnotes and endnotes, citations and bibliography, captions, cross-references, indexes, tables of authorities.
- **Review:** track changes, threaded comments, compare documents (legal blacklines), restrict editing, digital signatures.
- **Mailings, equations, charts, SmartArt, content controls and forms, building blocks.**
- **Reliability:** autosave, crash recovery, atomic saves, repair of damaged files.
- **Security:** blocking of external content and active content that Word has historically been attacked through.

## The Fidelity Contract

"Fidelity" means four different promises. Keeping them separate is what makes them achievable and testable.

### Tier A — Determinism (guaranteed)

For a given BayanDocs version, the same document lays out identically on Windows, macOS, Linux and every supported browser: every line break, every page break, every glyph position. The reference CPU rasterizer produces identical pixels everywhere.

- **How:** one engine compiled for every platform; integer layout arithmetic (ADR-0005); bundled fonts and our own shaping and rasterization instead of the operating system's (ADR-0009, ADR-0010, ADR-0011).
- **Condition:** the fonts the document needs are available, from the bundled library, from fonts embedded in the document, or from the organization's font library. If a document uses a font that exists only on one machine, BayanDocs says so and offers to embed it where its license allows.
- **Enforced by:** the determinism matrix in CI, which compares layout and pixel hashes across platforms on every change (ADR-0025).

### Tier B — Lossless round-trip (guaranteed)

Opening and saving a document never removes or alters anything BayanDocs did not deliberately edit: unknown elements, Microsoft extensions, custom XML, macros, embedded objects, comments metadata, revision history.

- **How:** unknown content is preserved and anchored in the document model; parts that were not touched are written back byte-for-byte; untouched paragraphs are written back verbatim (ADR-0007). Digital signatures that no longer match after an edit are reported, never silently dropped.
- **Enforced by:** round-trip tests, fuzzing, and periodic verification in Microsoft Word that re-saved files open without repair prompts.

### Tier C — Word fidelity (measured and published)

How closely BayanDocs matches Microsoft Word for Windows (a pinned reference build) is measured by the Fidelity Lab on public and private document corpora: page count, page-break agreement, line-break agreement, glyph position error, and visual difference.

- **How:** black-box study of Word's behavior with generated probe documents, written up as Word Behavior Notes and turned into tests (specs/fidelity-lab.md).
- **Targets:** rise phase by phase (plan/04-roadmap.md); each release publishes its scores.
- **User-facing:** the Fidelity Inspector tells a user when a document uses something BayanDocs does not yet reproduce exactly, so a surprise never reaches a recipient.

### Tier D — Reverse fidelity (designed for)

Documents created or edited in BayanDocs look the same when opened in Word.

- **How:** we write conservative, standards-conforming OOXML; we embed the open fonts we bundle when a Word user may not have them (Word honors embedded fonts); our own extensions are declared ignorable so Word skips them safely; the lab opens BayanDocs-authored documents in Word and measures them too.

### Layout versions

Within one release, Tier A is absolute. Across releases, layout may change only through deliberate, documented fidelity improvements, each tracked by an incrementing layout epoch number. Collaboration sessions require all participants to run the same layout epoch, so co-authors never see different pagination.

## Non-goals (for now)

- Spreadsheets and presentations. The engine's text components are reusable later, but no such product is planned.
- Phone-sized editing apps before 1.0. The web viewer works on phones; tablets get a Qt Quick shell after the editor matures.
- Server-side features that require reading document content. This is a deliberate consequence of zero-knowledge encryption.
- Bit-identical anti-aliasing under optional GPU rendering backends. Geometry stays identical; only edge pixels may differ, and the CPU renderer remains the reference.
- Decompiling or disassembling Microsoft software. All Word knowledge is clean-room.
- Bundling proprietary fonts.

## North-star metrics

| Area | Metric |
|---|---|
| Fidelity | Share of corpus documents whose page breaks match Word exactly, per corpus tier |
| Determinism | Cross-platform layout and pixel hash agreement (target: 100%) |
| Safety | Open data-loss bugs (target: 0); continuous fuzzing hours; round-trip integrity rate |
| Performance | Startup, open and keystroke-to-pixel latency against budgets |
| Accessibility | WCAG 2.2 AA conformance of the interface; PDF/UA validity of exports; screen-reader task success |
| Adoption (later) | Opt-in, privacy-preserving counts only |
