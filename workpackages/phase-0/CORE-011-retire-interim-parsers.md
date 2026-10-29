# CORE-011: Retire the interim parsers — bayan-opc's metadata on bayan-xml, the lab's scanner on bayan-opc and bayan-xml

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | FORMATS / LAB |
| Repository | bayan-core (`crates/bayan-opc/`, `lab/bayan-lab/`, `fuzz/`) |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | CORE-005, CORE-006, LAB-001 |
| Unblocks | LAB-101 (its corpus growth must not start collecting documents from the open web before this is merged) |
| Status | Ready |
| Requirements | SEC-01, SEC-07, FID-04 |
| Decisions | ADR-0002 (decision 6), ADR-0006, ADR-0025 |
| Specs | [fidelity-lab.md](../../specs/fidelity-lab.md) |

## Context

Two parsers were written as stand-ins until the real ones existed, and both outlived their replacements (architecture review of 2026-10-27, finding [M4](../../plan/reviews/2026-10-27.md#m4-two-interim-parsers-outlived-their-replacements)). Both are still in place at `3c5a18f`:

- **bayan-opc's own XML parser.** bayan-opc parses its three metadata parts (the content types stream, relationships parts and the core properties part) with a minimal parser of its own, [`crates/bayan-opc/src/xml.rs`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-opc/src/xml.rs#L3), 1,281 lines, which says that "once `bayan-xml` exists, the metadata parsers move onto it and this module is deleted". bayan-xml was merged on 2026-10-17 (CORE-006, `f32dfd6`), and FU-3 (`c7afbb2`) has since kept it within its documented memory bound on the two crafted inputs of finding M3. The crate documentation still says that bayan-xml "is still to be built" ([lib.rs:71](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-opc/src/lib.rs#L71)). bayan-opc depends only on cfb and miniz_oxide today; bayan-opc and bayan-xml are both in the Foundation layer ([plan/03 §4](../../plan/03-architecture.md#4-inside-bayan-core)), so bayan-opc may depend on bayan-xml, and bayan-xml does not depend on bayan-opc.
- **The Fidelity Lab's scanner.** bayan-lab's scanner reads packages with a ZIP reader, a CRC-32, a package reader and an XML reader of its own: `lab/bayan-lab/src/scan/zip.rs` (644 lines), `crc32.rs` (59), `opc.rs` (364) and `xml.rs` (943), "minimal stand-ins, written before `bayan-opc` (CORE-005) was merged, and marked for replacement" with no fuzz targets of their own ([lab/README.md:43](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/lab/README.md#L43)). The S3 store parses the listings of a bucket with the same XML reader ([store/s3.rs:12](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/lab/bayan-lab/src/store/s3.rs#L12)). The crafted packages in `lab/bayan-lab/tests/lab/hostile_packages.rs` test the scanner through its public interface.

**Why now.** LAB-101 will scan thousands of documents found on the open web, and the lab's reader, not the engine's, decides which of them enter the corpus. AGENTS.md §6 and ADR-0025 decision 4 ask every parser of untrusted input to be fuzzed, and ADR-0002 decision 6's rule against writing the same logic twice applies inside a repository too.

**What bayan-opc's metadata parsing promises**, which the move must keep: strict parsing of the three parts with the limits of `Limits` (above all `max_xml_nodes`, 250,000 nodes for all the metadata of a package together, and `max_metadata_total_size`), and the documented memory bound of opening a package and reading its core properties, at most about 256 MiB on top of the package's bytes ([lib.rs:63](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-opc/src/lib.rs#L63)); writing an unchanged metadata part back byte for byte, and a changed one with its own encoding, UTF-16 included (the test `keeps_utf16_streams_in_utf16`); and the properties that the fuzz targets `content_types`, `relationships` and `core_properties` check (unchanged, a part is written back byte for byte; changed, it parses again with the change; the change undone gives the input again). bayan-xml decodes UTF-8 and UTF-16 but its writer writes UTF-8 only, and says that a caller that must keep a part in UTF-16 converts the writer's output itself.

## Objective

bayan-opc reads its metadata parts with bayan-xml and its own XML parser is deleted; bayan-lab's scanner reads packages with bayan-opc and XML with bayan-xml and its four stand-ins are deleted; every parser that the lab runs on documents is fuzzed.

## Scope

### In scope

- **bayan-opc.** Parse the content types stream, relationships parts and the core properties part with bayan-xml's reader, keeping every promise listed above: the limits (count the nodes against `max_xml_nodes` as today, or with an equivalent budget that the documentation explains), the memory bound (measure it again with the crafted worst cases that the documentation describes, and update the figures), the exact round trip of unchanged parts, the encoding of changed parts, and the errors that tests and the public API name. Delete `src/xml.rs` and correct the crate documentation.
- **bayan-lab.** Open packages with bayan-opc (with limits suited to scanning, which the scanner's `Limits` maps onto bayan-opc's) and read the parts the tagger needs with bayan-xml's streaming reader; parse the S3 listings with bayan-xml. Delete `scan/zip.rs`, `scan/crc32.rs`, `scan/opc.rs` and `scan/xml.rs`. Keep `hostile_packages.rs` as the acceptance tests: they pass unchanged, or the pull request explains each change (for example a package that the lab used to accept and bayan-opc rightly refuses).
- **The same findings.** Regenerate the committed public corpus (`BAYAN_UPDATE_GENERATED=1 cargo test -p bayan-lab --test lab`): the manifests come out identical, or the pull request explains each difference, and `TAGGER_VERSION` rises as [the tagging rules](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/lab/corpus/tagging-rules.md) require when what a document is tagged with changes.
- **A fuzz target for the scanner**, `lab_scan`, which runs the scanner's entry point (`scan`) on the input with the scanner's default limits, with settings in `TARGETS` of `fuzz/ci.py`, seeds made like those of `package`, and `lab/bayan-lab/**` in `fuzz.yml`'s path filter. bayan-lab is a member of the main workspace, so the fuzz workspace may depend on it by path.
- **Documentation.** bayan-opc's crate documentation, `lab/README.md`, the targets table of `fuzz/README.md` (the three metadata targets now fuzz bayan-xml underneath) and bayan-core's `AGENTS.md`.

### Out of scope

- New features in the scanner or the tagger.
- Changes to bayan-xml beyond what bayan-opc needs from it; a missing capability that would take more than a small addition is a reason to stop and ask (see below).
- Time budgets and cancellation (finding H6, an ADR-0006 amendment for the Phase-0 gate).

## Deliverables

- bayan-opc and bayan-lab on bayan-xml and bayan-opc, with the five interim modules deleted.
- The `lab_scan` fuzz target and its settings.
- Regenerated public corpus manifests if anything changed, and the documentation above.

## Acceptance criteria

- [ ] AC-1 `crates/bayan-opc/src/xml.rs` is deleted and bayan-opc's tests pass; any test that changed is explained in the pull request.
- [ ] AC-2 The metadata limits still hold: tests with crafted parts that reach `max_xml_nodes` and `max_metadata_total_size` are refused as before, and the documented memory bound is measured again on 64-bit Linux, with the new figures in the crate documentation and the pull request.
- [ ] AC-3 `writes_the_same_bytes_every_time_on_every_platform` and `keeps_utf16_streams_in_utf16` pass unchanged, and the fuzz targets `content_types`, `relationships` and `core_properties` keep their properties (the pull request's `fuzz.yml` run).
- [ ] AC-4 `lab/bayan-lab/src/scan/zip.rs`, `crc32.rs`, `opc.rs` and `xml.rs` are deleted; `hostile_packages.rs` passes; the S3 store's tests pass with the listings parsed by bayan-xml.
- [ ] AC-5 Regenerating the public corpus gives identical manifests, or each difference is explained and `TAGGER_VERSION` rises as the tagging rules say.
- [ ] AC-6 `lab_scan` builds and runs in `fuzz.yml` on the pull request, and ran for at least 30 minutes in the session without a failure, or each failure is fixed with a regression test.
- [ ] AC-7 `cargo xtask verify` passes, and the change adds no package to either `Cargo.lock`.

## Verification

`cargo xtask verify`; `cargo test -p bayan-opc`; `cargo test -p bayan-lab --test lab`; `BAYAN_UPDATE_GENERATED=1 cargo test -p bayan-lab --test lab` followed by `git diff --stat lab/corpus/`; the fuzzing commands of `fuzz/README.md` for `lab_scan` and the three metadata targets.

## Notes and pitfalls

- bayan-opc's metadata writer edits parts in place from the spans of its nodes. bayan-xml's events carry exact byte spans in the decoded text; for a UTF-16 part, work out how spans in the decoded text map back to the original bytes before relying on them.
- bayan-opc's documentation explains why the metadata tree costs a few hundred bytes per node; a streaming reader may need much less, but the bound must be measured, not assumed.
- The lab must keep treating every document as hostile: a document that bayan-opc refuses is recorded as refused, never scanned with a weaker reader.
- bayan-lab is native only (`NATIVE_ONLY`); bayan-opc and bayan-xml are also built for WebAssembly, and nothing in this change may make them depend on bayan-lab.
- CORE-010 also changes `fuzz/` and `fuzz.yml`; the two work packages should not run at the same time.

## Escalate if

- Keeping bayan-opc's round trip or memory bound needs more from bayan-xml than a small addition, such as a change to its public API that CORE-006 did not plan.
- The public corpus's findings change in a way that the tagging rules do not cover.
- bayan-opc's limits refuse documents that the lab needs to study, so that the scanner would need limits looser than bayan-opc's defaults.
