# LAB-004: Comparison metrics and fidelity report

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | LAB |
| Repository | bayan-core (`lab/`) |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | LAB-003 |
| Unblocks | LAB-106 (fidelity gate), every fidelity claim |
| Status | Ready |
| Requirements | FID-04 |
| Decisions | ADR-0004, ADR-0025 |
| Specs | [fidelity-lab.md §6, §9](../../specs/fidelity-lab.md#6-comparison-and-metrics) |

## Context

The lab spec defines metrics M1–M7 and how they gate pull requests. Before the engine can lay out real documents, the comparison pipeline can already be built and tested on synthetic pairs and wired into CI with placeholder engine output.

## Objective

A comparison tool implementing the metrics, aggregated reports, and a CI job ready to become the fidelity gate in Phase 1.

## Scope

### In scope

- `bayan-lab compare`: align the two text streams per document (diff tolerant of small differences such as numbering labels and field results), then match pages, lines and glyphs.
- Metrics M1–M4 and M7 implemented; M5 (visual difference) defined with an interface and a basic implementation or a documented stub if PDF rasterization is not yet available; M6 is a reference-machine process documented here.
- Aggregation by tier, feature tag, script and compatibility mode; worst-document lists; correlation of disagreement with feature tags.
- Reports: static HTML (no external assets or scripts from other origins) and JSON summary; comparison with a stored baseline to detect regressions.
- CI job that runs over the public corpus using whatever layout JSON the engine can produce (initially empty or trivial, giving zero scores) and publishes the report as an artifact.

### Out of scope

Making scores good (that is Phase 1).

## Deliverables

Comparison tool, report generator, CI job, documentation.

## Acceptance criteria

- [ ] AC-1 Unit tests with synthetic pairs whose differences are known (shifted page break, changed line break, offset glyphs, missing text) produce exactly the expected metric values.
- [ ] AC-2 The HTML report renders offline and lists per-tier, per-feature and worst-document results.
- [ ] AC-3 The CI job runs and uploads the report and JSON summary.
- [ ] AC-4 Regression detection flags a document that loses agreement relative to the baseline.

## Verification

`cargo xtask verify`; CI artifact link.

## Escalate if

The alignment approach cannot handle common differences (for example field results that legitimately differ such as dates); propose normalization rules for the spec.
