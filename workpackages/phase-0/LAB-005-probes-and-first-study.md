# LAB-005: Probe generator and the first Word measurement study

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | LAB / TEXT |
| Repository | bayan-core (`lab/`, `spikes/` or `bayan-text`) and docs (Word Behavior Notes) |
| Attach to session | bayan-core, docs |
| Size | L |
| Depends on | LAB-002, LAB-003, CORE-003 |
| Unblocks | CORE-111, CORE-112 (Word measurement model and line breaking) |
| Status | Ready |
| Requirements | FID-04, TYP-02 |
| Decisions | ADR-0009 (§5 Word measurement model), ADR-0005, ADR-0004 |
| Specs | [fidelity-lab.md §8](../../specs/fidelity-lab.md#8-reverse-engineering-method-word-behavior-notes), [word-behavior/](../../specs/word-behavior/README.md) |

## Context

The measurement model (how Word turns font units into advances, where it rounds, how it computes line heights, when it kerns) is the foundation of line-break agreement. This first study establishes the reverse-engineering method and answers the three most basic questions, WBN-0001 to WBN-0003.

## Objective

A reusable probe generator, three confirmed Word Behavior Notes, and a prototype implementation that reproduces Word's line breaks on the probe set with Word's own fonts.

## Scope

### In scope

- **Probe generator** (Rust): writes minimal valid `.docx` files from parameters (font, size, text pattern, paragraph width via margins or indents, spacing, kerning flag, ligature settings, compatibility mode), recording parameters in the corpus manifest as T0 documents.
- **WBN-0001 (advances and rounding):** probes varying string content and length, font size (for example 8–72 pt including fractional half-points), and width, for the most common fonts; observe where Word breaks lines; infer how advances are scaled, rounded and accumulated.
- **WBN-0002 (line height):** probes for single, multiple ("auto"), exact and at-least spacing across fonts and sizes; infer which font metrics Word uses and how it rounds.
- **WBN-0003 (kerning and ligatures defaults):** when Word applies kerning and ligatures by default and how `w:kern` and `w14:ligatures` change it.
- Notes written with the template, including probes, observations, rules and confidence.
- **Prototype:** implement the rules in the CORE-003 pipeline (or an early `bayan-text`), run it on the reference machine with Word's own fonts (algorithm fidelity), and measure agreement on the probes.
- Add the probes to the T0 corpus with their ground truth.

### Out of scope

Paragraph features beyond spacing (tabs, justification: Phase 1 LAB-102).

## Deliverables

Probe generator, three notes in `docs/specs/word-behavior/`, prototype rules, study report.

## Acceptance criteria

- [ ] AC-1 WBN-0001, WBN-0002 and WBN-0003 are written with High confidence, or with an explicit account of what remains unexplained.
- [ ] AC-2 With Word's own fonts on the reference machine, the prototype reproduces Word's line breaks on at least 99% of the probe set and line heights exactly.
- [ ] AC-3 Probes and ground truth are stored in T0 and runnable as regression tests.
- [ ] AC-4 No Microsoft font data leaves the reference machine.

## Verification

Study report with metric tables; tests runnable in CI with the open-font variants of the probes.

## Escalate if

Observations cannot be explained by any consistent rule after systematic bisection; describe the anomalies so the planner can decide how to proceed.
