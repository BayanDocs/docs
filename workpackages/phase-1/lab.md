# Phase 1 — Faithful Viewer: Fidelity Lab work packages (drafts)

**Status: Draft**, refined at the Phase-0 gate. All in bayan-core (`lab/`) with Word Behavior Notes in docs; attach bayan-core and docs. Studies run on the owner's reference machine.

### LAB-101 — Corpus growth and private corpus
- **Size:** M · **Depends on:** LAB-001, owner decision on private storage
- **Scope:** grow the public corpus to 2,000 documents with balanced feature coverage (scripts, compatibility modes, document types); set up the private corpus (10,000+ documents, aggregate reporting only); the torture tier (300 documents); weekly frequency reports feeding the coverage matrix priorities.

### LAB-102 — Word study: paragraphs and lines
- **Size:** L · **Depends on:** LAB-005
- **Scope:** WBN-0004 (line-break tailoring), WBN-0005 (tabs), WBN-0006 (justification), plus spacing interactions (contextual spacing, automatic spacing, spacing at page tops); probes and notes; feeds CORE-112 and CORE-113.

### LAB-103 — Word study: tables
- **Size:** L · **Depends on:** LAB-005
- **Scope:** WBN-0007 (autofit), border conflict resolution, cell margins and spacing, row height rules, row splitting; feeds CORE-115.

### LAB-104 — Word study: floating objects and wrapping
- **Size:** L · **Depends on:** LAB-005
- **Scope:** WBN-0008: positioning in every reference frame, each wrap mode, polygons, overlap, objects in table cells; feeds CORE-116.

### LAB-105 — Word study: pagination and notes
- **Size:** M · **Depends on:** LAB-005
- **Scope:** WBN-0009: keep rules, widow and orphan control, page breaks before, footnote placement and continuation, column balancing; feeds CORE-113, CORE-117, CORE-118.

### LAB-106 — Fidelity gate activation
- **Size:** S · **Depends on:** LAB-004, CORE-113
- **Scope:** turn on the pull-request fidelity gate (ADR-0025) with stored baselines and the `fidelity-change` label process; nightly full runs.

### LAB-107 — Determinism matrix as a permanent gate
- **Size:** S · **Depends on:** CORE-003, CORE-121
- **Scope:** promote the spike's matrix to a permanent gate over the determinism corpus on every pull request (subset) and nightly (full).

### LAB-108 — Round-trip verification in Word
- **Size:** M · **Depends on:** LAB-002, CORE-107
- **Scope:** on the reference machine, open every BayanDocs re-saved public-corpus document in Word and confirm no repair prompt and identical content; report failures as defects.

### LAB-109 — Public fidelity dashboard
- **Size:** S · **Depends on:** LAB-106
- **Scope:** publish public-corpus fidelity reports (static pages on the docs site) per release and nightly, with trends; never private-corpus details.
