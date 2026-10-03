# CORE-005: `bayan-opc` — hardened package layer

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | FORMATS / SECURITY |
| Repository | bayan-core |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | CORE-001 |
| Unblocks | CORE-102…CORE-107 (DOCX import/export), LAB-001 tagging |
| Status | Ready |
| Requirements | FID-01, FID-03, SEC-01, SEC-02, REL-05 |
| Decisions | ADR-0006, ADR-0017, ADR-0018 |
| Specs | [threat-model.md](../../specs/threat-model.md) (T1, T3) |

## Context

Every `.docx` is an Open Packaging Conventions (OPC) package: a ZIP archive with content types and relationships (ECMA-376 Part 2). The ZIP layer is the first code to touch hostile bytes, so it must be strict, limited and fuzzed. Research on 2026-10-03 found the popular `zip` crate has had frequent major versions, unexplained yanks and a 2025 path-traversal CVE, and pulls a C compression library by default; `rc-zip` is a read-only, I/O-agnostic alternative. Round-trip fidelity (Tier B) requires writing untouched parts back unchanged.

## Objective

A safe, limited, fuzzed OPC reader and deterministic writer that can copy untouched parts verbatim.

## Scope

### In scope

- **ZIP reading** via a justified choice: `rc-zip`, `zip` with default features off and pure-Rust deflate only, or a small in-house reader. Requirements: ZIP64, data descriptors, deflate and stored entries via pure-Rust decompression; rejection of encrypted entries, symbolic links, absolute paths, `..` segments, duplicate names (including names equivalent under OPC's case-insensitive part-name rules); configurable limits (entry count, per-entry and total uncompressed size, compression ratio, name length) with safe defaults.
- **ZIP writing:** deterministic output (fixed timestamps, stable entry order, fixed compression level), and **raw copy** of an original entry's compressed bytes for untouched parts.
- **OPC:** `[Content_Types].xml` parsing and writing (defaults and overrides), package and part relationships (preserving unknown attributes and order), part-name normalization and validation per ECMA-376 Part 2, relationship target resolution distinguishing internal and external targets (external targets are recorded, never fetched), core properties (minimal).
- **Compound File Binary (OLE)** read-only access through the `cfb` crate (or justified alternative) behind a small API, for later use with `.doc`, VBA projects and encrypted packages; only an API and tests now.
- Fuzz targets for the ZIP reader, content types and relationships parsers.
- Tests with synthetic packages (including crafted zip bombs, traversal names, duplicate names) and a handful of small real `.docx` files with recorded licenses.

### Out of scope

XML parsing beyond what the content-types and relationships parts need (use `bayan-xml` if CORE-006 has landed, otherwise a minimal internal parser marked for replacement), DOCX semantics, encryption.

## Deliverables

The `bayan-opc` crate, fuzz targets under `fuzz/`, tests, documentation of limits.

## Acceptance criteria

- [ ] AC-1 Reading and re-writing an unmodified package with raw copy yields identical bytes for every part (and identical uncompressed content for regenerated metadata parts).
- [ ] AC-2 Each crafted malicious package is rejected with a specific error, within limits, without excessive memory use.
- [ ] AC-3 Fuzz targets ran for at least one CPU-hour in total without crashes (evidence in the pull request).
- [ ] AC-4 No `unsafe`, no C dependencies (verified by `cargo tree` output in the pull request).
- [ ] AC-5 The dependency choice is justified against the alternatives above.

## Verification

`cargo xtask verify`; fuzz commands and durations recorded.

## Escalate if

No ZIP option meets the requirements without C code or `unsafe` in the dependency; propose writing the reader in-house with an estimate.
