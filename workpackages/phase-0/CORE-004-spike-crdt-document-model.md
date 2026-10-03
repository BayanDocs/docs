# CORE-004: Spike — Word-shaped document model on Loro

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | MODEL / SYNC |
| Repository | bayan-core |
| Attach to session | bayan-core, docs |
| Size | L |
| Depends on | CORE-001 |
| Unblocks | CORE-101 (model v1), all editing and collaboration work |
| Status | Ready |
| Requirements | FID-03, COL-01, COL-03, PERF-03, PERF-05 |
| Decisions | ADR-0007 and ADR-0008 (this spike is their validation gate), ADR-0005, ADR-0006 |
| Specs | [document-model.md](../../specs/document-model.md) (especially §4, §5, §7, §14, §16, §18) |

## Context

ADR-0007 models documents as Word does internally: stories of atoms where paragraph ends, field delimiters and anchors are characters, with tables as objects whose cells own stories. ADR-0008 stores that model in Loro behind a `bayan-crdt` adapter. Both are accepted subject to this spike. The spec's §18 lists the open questions this spike must answer.

## Objective

Implement a minimal but representative BDM on Loro, prove convergence and deterministic normalization under randomized concurrent editing, measure performance at realistic scale natively and in WebAssembly, and recommend confirming or amending ADR-0007/0008.

## Scope

### In scope

- `bayan-crdt` adapter prototype exposing BDM-shaped primitives (story sequences with marks and placeholder atoms, property maps, movable row lists, cell lists, undo manager, snapshots, checkout). Loro must not be visible outside the adapter.
- Minimal `bayan-model` with: atoms Text, ParagraphEnd, Tab, FieldBegin/Separator/End, ObjectAnchor, RangeStart/End, TableBlock; marks for several run properties (expand after), hyperlink (none), comments `cmt:<id>` (none), revisions (none); paragraph property maps; tables with movable row lists and per-cell stories; an objects map.
- Operations: insert text, delete range, format range, split and merge paragraphs, insert table, insert/delete/move rows, insert/delete columns, add comment over a range, insert field.
- Normalization N1–N7 as a pure function producing a view; invariants I1–I7 checked on the view.
- Property-based tests: three replicas apply random operations (including concurrent structural edits), exchange updates in random orders with partitions, and must end with identical views satisfying I1–I7. Target: 1,000 runs of 10,000 operations (a smaller default in CI; the full run documented in the report). Normalization must be shown deterministic and idempotent.
- Undo tests: undo reverts only local changes and composes with remote edits sensibly.
- Mark-expansion tests matching the expectations in spec §5 (including many overlapping comments).
- Performance on a synthetic 500-page document (about 1.5 million characters, 15,000 paragraphs, 200 tables, 2,000 comments): load from snapshot, memory, applying a 1,000-operation update, snapshot and update sizes, natively and in wasm32 under Node. Initial targets, to be confirmed or revised with justification: load ≤ 300 ms native and ≤ 1 s in WebAssembly; applying 1,000 operations ≤ 50 ms; WebAssembly memory ≤ 300 MB.
- A fuzz target importing untrusted Loro updates through the adapter with resource limits.
- A time-boxed comparison on Automerge 3 for the text-with-marks-and-block-markers subset and the same performance measurements.
- A report in `spikes/crdt-model/REPORT.md` answering every question in spec §18, and a docs pull request updating the spec and the validation status of ADR-0007/0008.

### Out of scope

DOCX import, layout, production-quality APIs beyond the adapter's shape.

## Deliverables

Adapter and model prototypes, tests, fuzz target, benchmarks, report, docs pull request.

## Acceptance criteria

- [ ] AC-1 100% of randomized runs converge to identical, invariant-satisfying views (evidence: test output and the full-run log summary).
- [ ] AC-2 Normalization is proven deterministic and idempotent by property tests.
- [ ] AC-3 Undo and mark-expansion tests pass.
- [ ] AC-4 Performance figures are reported against the targets, natively and in WebAssembly, with an explanation for any miss.
- [ ] AC-5 The fuzz target runs for at least one CPU-hour without crashes (or crashes are reported upstream with minimal reproductions and mitigated by limits).
- [ ] AC-6 Every question in spec §18 has an answer or a clearly scoped follow-up.

## Verification

`cargo xtask verify`; benchmark commands documented in the report.

## Notes and pitfalls

- Placeholder code points must never leak into exported text or accessibility output.
- Use seeded randomness so failing runs are reproducible; shrink failing cases.

## Escalate if

Convergence or performance fails in ways that suggest the model shape itself is wrong (rather than an implementation bug); the planner will decide on amending ADR-0007 or switching to the fallback in ADR-0008.
