# LAB-002: Word ground-truth harness on the reference machine

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | LAB |
| Repository | bayan-core (`lab/word-harness/`) |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | LAB-001; **owner provides the reference machine** (owner checklist item 9) |
| Unblocks | LAB-005, CORE-008, all Tier C measurement |
| Status | Ready (needs owner hardware) |
| Requirements | FID-04, FID-06 |
| Decisions | ADR-0004 (§5 reference definition), ADR-0025 |
| Specs | [fidelity-lab.md §4](../../specs/fidelity-lab.md#4-ground-truth-reference-machine), [§12](../../specs/fidelity-lab.md#12-legal-and-ethical-notes) |

## Context

Microsoft Word on a dedicated Windows machine is the lab's measuring instrument. Ground truth is produced once per document per Word build and stored; CI never runs Word. The machine processes documents from the open internet, so it must be isolated and locked down. Clean-room rule: observe outputs only.

## Objective

A documented reference-machine configuration and a robust, resumable harness that turns corpus documents into Word ground truth (PDF, layout skeleton, re-saved copy, metadata).

## Scope

### In scope

- **Configuration guide** (`lab/word-harness/REFERENCE-MACHINE.md`): Windows 11; Microsoft 365 Apps installed and pinned to a specific build with the Office Deployment Tool; Trust Center settings (macros disabled without notification, external content blocked, Protected View behavior chosen and documented); AutoSave, OneDrive and cloud features off; add-ins disabled; font inventory captured; no personal data; network policy for the machine; how to update and re-baseline.
- **Harness** in PowerShell using Word's COM automation (run only on the reference machine): open each document read-only without adding to recent files and without repair or conversion prompts; wait for pagination to complete; export PDF with document structure tags; extract a layout skeleton (page count, page-start character positions, line starts for sampled paragraphs) through the object model; save a re-saved copy in the same format without changing the compatibility mode; record Word build, Windows build, timing and any prompts or errors.
- **Robustness:** per-document timeout, detection and dismissal of modal dialogs, killing and restarting Word on hangs, resumable batches, a log of failures.
- **Output layout** in the ground-truth store matching LAB-001's manifest conventions, plus a transfer procedure from the isolated machine to storage (archive with checksums).
- Output skeletons conform to the LAB-003 layout JSON schema (fields Word cannot provide are marked absent).

### Out of scope

PDF glyph extraction (LAB-003), comparisons (LAB-004).

## Deliverables

Configuration guide, harness scripts, run report for the public corpus.

## Acceptance criteria

- [ ] AC-1 The harness processes at least 300 T1 documents end to end; failures are logged with reasons.
- [ ] AC-2 Running the same document twice yields identical outputs apart from timestamps (determinism of the instrument).
- [ ] AC-3 Outputs validate against the LAB-003 schema.
- [ ] AC-4 The configuration guide lets the owner reproduce the setup on a fresh machine.

## Verification

Run logs and summary statistics in the pull request (no private documents).

## Notes and pitfalls

- COM automation of Word is slow for line-level extraction; sample lines rather than walking every character, and rely on the PDF for glyph positions.
- Keep the harness free of third-party PowerShell modules where possible; any module needed is pinned and checksummed.

## Escalate if

The reference machine is not available (the brief cannot start); licensing terms of the owner's Microsoft 365 plan appear to restrict this use.
