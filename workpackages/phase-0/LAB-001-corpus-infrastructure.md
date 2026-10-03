# LAB-001: Corpus infrastructure and public corpus v1

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | LAB |
| Repository | bayan-core (`lab/`) |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | CORE-001 (uses CORE-005/006 if merged; otherwise a minimal scanner) |
| Unblocks | LAB-002, CORE-008, coverage prioritization |
| Status | Ready |
| Requirements | FID-04 |
| Decisions | ADR-0004, ADR-0025, ADR-0003 (license compatibility of test data) |
| Specs | [fidelity-lab.md §3](../../specs/fidelity-lab.md#3-corpus-tiers), [coverage-matrix.md](../../specs/coverage-matrix.md) |

## Context

Every fidelity number depends on the corpus. Documents must be identified by hash, carry their provenance and license, and be tagged with the features they use so that results can be broken down by feature and so that the coverage matrix can be prioritized by real frequency. Corpus files live outside Git; only manifests are committed.

## Objective

Corpus tooling (manifest, content-addressed storage, verification, feature tagging) and a public T1 corpus of at least 300 `.docx` documents with recorded, compatible licenses.

## Scope

### In scope

- **Manifest schema** (JSON, documented): SHA-256 identifier, source and provenance, SPDX license, tier, detected features (using coverage-matrix feature names), languages and scripts, compatibility mode, fonts referenced, size, page count once known, ground-truth status, notes.
- **CLI** (`bayan-lab corpus …`): `add` (hash, deduplicate, record provenance and license), `verify` (hashes and manifest consistency), `tag` (feature tagging), `list`/`stats` (frequencies by feature, font, script, compatibility mode).
- **Storage:** content-addressed layout (`objects/ab/cdef….docx`) with a local-directory backend and an S3-compatible backend behind one interface; the public corpus location is proposed for the owner to create.
- **Feature tagging** by scanning package parts and element names (safely, with limits), mapping to coverage-matrix names.
- **Public T1 corpus v1:** at least 300 documents from sources with licenses compatible with redistribution in our context, for example the test files of Apache POI (Apache-2.0), the Open XML SDK (MIT), LibreOffice's Writer test documents (MPL-2.0), docx4j and python-docx test files, public-domain government documents, and documents authored by agents for the project. Each document's license is recorded per file; documents with unclear licenses are excluded.
- **Private corpus (T2) options** document for the owner: storage choices, access control, legal and privacy considerations, and a proposed collection method.

### Out of scope

Ground truth (LAB-002), comparisons (LAB-004).

## Deliverables

Lab crate with CLI, manifest schema documentation, public corpus manifest committed to the repository (files in storage), T2 options document, frequency report.

## Acceptance criteria

- [ ] AC-1 At least 300 T1 documents with complete manifest entries and per-file licenses; `corpus verify` passes.
- [ ] AC-2 Feature tags are produced for every document; a frequency report by feature, font and script is generated.
- [ ] AC-3 The tagger handles malformed and malicious packages within limits (tests with crafted files).
- [ ] AC-4 The T2 options document is ready for the owner's decision.

## Verification

`cargo xtask verify`; `bayan-lab corpus verify` and `stats` output in the pull request.

## Escalate if

A promising source's license is ambiguous; do not include it, and list it under open questions.
