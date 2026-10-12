# ADR-0009: Text stack — shaping, Unicode, line breaking and the Word measurement model

- **Status:** Accepted — validated by CORE-003 (2026-10-12)
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** FID-02, TYP-01, TYP-02, I18N-01…I18N-04, ADR-0005, ADR-0010, CORE-003, LAB-005

## Context

Text layout is where fidelity is won or lost. We need deterministic shaping for every script, Unicode segmentation and bidirectional ordering, hyphenation, and above all a line breaker that makes the same decisions as Word, which uses greedy (first-fit) line breaking with its own tailoring, rounding and compatibility options. Ecosystem facts verified on 2026-10-03:

- **harfrust** 0.13.3 (MIT), maintained by the HarfBuzz project: a pure-Rust port of HarfBuzz (tracking HarfBuzz 14.x), no `unsafe`, shapes in font units (integer output), used by parley, cosmic-text and resvg. **rustybuzz** is archived and **ttf-parser** is in maintenance mode; RustSec marks both unmaintained and points to harfrust and skrifa.
- **read-fonts / skrifa** (Google's fontations, MIT/Apache-2.0): font parsing, outlines (TrueType, CFF, CFF2, variations, hinting, COLR), fuzzed on OSS-Fuzz; Chrome uses skrifa instead of FreeType.
- **ICU4X** 2.x (Unicode-3.0 license): grapheme, word, sentence and line segmentation (UAX #14/#29), locale data. It provides no bidi algorithm itself but feeds Bidi_Class data to the **unicode-bidi** crate. Southeast Asian word breaking offers LSTM or dictionary models.
- **hypher** 0.1.8 (MIT/Apache-2.0, Typst): TeX hyphenation patterns for 48 languages, only permissively licensed patterns.
- **parley** (Linebender): a general text layout library; not Word-compatible line breaking, no hyphenation, frequent breaking releases.

## Decision

1. **Shaping:** harfrust. **Font parsing, metrics and outlines:** read-fonts and skrifa. One font parser across shaping, measurement, rendering and PDF subsetting.
2. **Segmentation:** ICU4X `icu_segmenter`, using the **dictionary** models (not LSTM) for Thai, Lao, Khmer and Burmese, because the LSTM path involves floating-point inference that we cannot guarantee to be bit-identical. Locale data is sliced to what we ship.
3. **Bidirectional text:** unicode-bidi with ICU4X data, plus Word-specific behaviors documented in Word Behavior Notes.
4. **Line breaking:** our own greedy line breaker in `bayan-text`/`bayan-layout`, starting from UAX #14 opportunities and applying Word's tailoring as discovered by the Fidelity Lab: treatment of spaces and trailing whitespace, hyphens and dashes, non-breaking and optional hyphens, East Asian rules (kinsoku, including custom `w:noLineBreaksBefore/After` lists), automatic spacing between Asian and Latin text, character grids, and compatibility options. Optimal (Knuth–Plass-style) breaking is **only** an opt-in for BayanDocs-native documents (TYP-03).
5. **The Word measurement model** is a first-class component: the exact rules by which Word turns font units into advances, where it rounds, how it accumulates widths along a line, how it computes line heights from font tables (for example which ascent and descent values it uses), how justification distributes space (including kashida), and how compatibility options alter these. Each rule is backed by a Word Behavior Note with probe evidence and is implemented in BLU (ADR-0005).
6. **OpenType features** are applied exactly when Word applies them (for example, kerning only when the document enables it at the given size; ligatures according to `w14:ligatures`), so Word documents never change because our typography is "better".
7. **Hyphenation:** hypher for the languages it covers; additional languages via downloadable pattern packs after license review. Word's own hyphenation dictionaries are proprietary, so documents with automatic hyphenation are a known fidelity risk to be measured.
8. parley and fontique may be used as references or in non-layout UI contexts only; fontique's `system` feature (which calls platform font APIs) must never be enabled in the core.

## Consequences

- Shaping and parsing come from actively maintained, memory-safe, Google- and HarfBuzz-backed code.
- The line breaker and measurement model are ours to build and the core of the Fidelity Lab's work; this is the project's main research investment.
- Pure-Rust ICU4X data adds a few megabytes; slicing keeps the WebAssembly download within budget.

## Alternatives considered

- **HarfBuzz and FreeType (C/C++):** the reference implementations, but contrary to ADR-0006 for untrusted fonts.
- **Platform shapers (DirectWrite, Core Text):** nondeterministic across platforms; unavailable in WebAssembly.
- **rustybuzz / ttf-parser:** unmaintained.
- **parley for layout:** its line breaking and paragraph model are not Word's.

## Validation gate

CORE-003 must show identical shaping, line-breaking and layout hashes on Linux x86-64, Windows x86-64, macOS arm64 and wasm32 for the probe set (Latin, Arabic, Hebrew, Devanagari, Thai, Chinese, Japanese, mixed bidi), and report shaping throughput and WebAssembly size.

## Validation result (CORE-003, 2026-10-12)

The gate is met, and the decisions stand as written. The [CORE-003 report](https://github.com/BayanDocs/bayan-core/pull/18) (`spikes/text-pipeline/REPORT.md` in bayan-core) has the evidence.

- **Identical output in eleven environments.** For the gate's 30 probes (Latin with kerning on and off and with ligatures, Arabic with marks, Hebrew with numbers and Latin, Devanagari, Thai broken with the dictionary model, Chinese, Japanese, and mixed bidi in both directions) and for a full 3840 × 2160 screen of text, the layout (every glyph's identifier and position in BLU, and every line box) had the same SHA-256 natively on Linux x86-64, Windows x86-64 and macOS arm64, and in WebAssembly, built with and without SIMD, in Node.js 24 on the same three systems and in headless Chromium 153 (the pull request's first CI run, on 2026-10-12). The pipeline itemizes with unicode-bidi on ICU4X's data, segments with ICU4X's dictionary models, shapes with harfrust (kerning on and off), measures in BLU with `bayan-units`, breaks lines first-fit at UAX #14 opportunities and reorders each line with the bidi algorithm. bayan-core's verification gate now checks three of the probes, those whose fonts are small enough to commit, on every pull request, natively and in WebAssembly; its `text-pipeline` workflow runs the whole set whenever the stack or its pins change, and weekly.
- **The settings that make it so**, which the production crates keep: read-fonts, skrifa and harfrust are built with their `libm` feature instead of `std`, so that the one transcendental function they call (`hypot`, for the offsets of transformed components in composite glyphs) comes from pure Rust (ADR-0005 §4); `icu_segmenter` is built without its `lstm` and `auto` features, so that the LSTM code is not even compiled (Decision 2); unicode-bidi is built without `hardcoded-data`, so that one Unicode version serves bidi, scripts and segmentation (Decision 3). ICU4X's data crates replace their compiled data with the contents of the folder that `ICU4X_DATA_DIR` names when that variable is set at build time; the first work package that ships ICU4X makes the gate and the artifact builds refuse it.
- **Throughput:** on one core, shaping runs at 2.4 to 3.7 million characters per second natively and 1.7 to 2.4 million in WebAssembly, over all the gate's scripts; with itemization, segmentation, line breaking and layout, at 1.3 to 1.7 and 0.9 to 1.3 million.
- **WebAssembly size:** the stack adds about 1.1 MB with brotli to a module (read-fonts and skrifa 136 KB, harfrust 129 KB, ICU4X's code 17 KB, unicode-bidi 5 KB, and data, mostly ICU4X's, 823 KB). ICU4X's four line-break dictionaries, for Burmese, Khmer, Lao and Thai, are 1.77 MB of the module's 2.16 MB of data before compression, so slicing the data (Decision 2) and loading those dictionaries only when a document needs them keep the engine well within PERF-06.
- **Not part of this gate:** Word's line breaking and measurement model (Decisions 4 and 5) and the rules for applying OpenType features (Decision 6), which LAB-005, CORE-008 and Phase 1 build on this stack.

## Revisit when

harfrust or fontations lose maintenance, or the lab finds Word behaviors that require capabilities these libraries cannot provide.
