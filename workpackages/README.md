# Work Packages

A work package (WP) is a self-contained brief that one agent session can execute and deliver as a pull request. Briefs follow [TEMPLATE.md](TEMPLATE.md). How to hand one off, review it and mark it done is described in [plan/06-agent-workflow.md](../plan/06-agent-workflow.md).

**Identifiers** are stable: `CORE-`, `LAB-` (Fidelity Lab, in bayan-core), `DESK-`, `WEB-`, `SRV-`, `DOCS-`, and `X-` (cross-repository). Numbers 001–099 were planned for Phase 0, 101–199 for Phase 1, and so on; a WP keeps its number if it moves.

**Status values:** Draft · Ready · In progress · In review · Done · Blocked. The reviewer session updates this table after each merge.

## Phase 0 — Bedrock

| ID | Title | Repo | Size | Depends on | Wave | Status |
|---|---|---|---|---|---|---|
| [X-001](phase-0/X-001-repository-baseline.md) | Repository baseline: governance files, PR template, DCO, REUSE check | all | M | — | 1 | Done |
| [DOCS-001](phase-0/DOCS-001-knowledge-base-site.md) | Knowledge-base site (mdBook) and docs CI | docs | S | — | 1 | Done |
| [CORE-001](phase-0/CORE-001-workspace-and-gate.md) | Core workspace scaffold and verification gate | core | M | — | 1 | Done |
| [DESK-001](phase-0/DESK-001-desktop-scaffold.md) | Desktop scaffold and CI | desktop | M | — | 1 | Done |
| [WEB-001](phase-0/WEB-001-web-scaffold.md) | Web scaffold and CI | web | M | — | 1 | Done |
| [SRV-001](phase-0/SRV-001-server-scaffold.md) | Server scaffold, container and CI | server | M | — | 1 | Done |
| [X-002](phase-0/X-002-ci-security-baseline.md) | CI security baseline | all | S | scaffolds | 2 | Ready |
| [X-003](phase-0/X-003-supply-chain-enforcement.md) | Supply-chain enforcement and update runbook | all code repos | M | CORE-001, SRV-001, WEB-001, DESK-001 | 2 | Ready |
| [CORE-002](phase-0/CORE-002-bayan-units.md) | `bayan-units` | core | S | CORE-001 | 2 | Done |
| [CORE-004](phase-0/CORE-004-spike-crdt-document-model.md) | Spike: document model on Loro | core | L | CORE-001 | 2 | Ready |
| [CORE-005](phase-0/CORE-005-bayan-opc.md) | `bayan-opc` | core | M | CORE-001 | 2 | Ready |
| [CORE-006](phase-0/CORE-006-bayan-xml.md) | `bayan-xml` | core | M | CORE-001 | 2 | Ready |
| [CORE-007](phase-0/CORE-007-engine-skeleton.md) | Engine skeleton: protocol v0, C ABI, WebAssembly | core | L | CORE-001 | 2 | Ready |
| [LAB-001](phase-0/LAB-001-corpus-infrastructure.md) | Corpus infrastructure and public corpus v1 | core | M | CORE-001 | 2 | Ready |
| [LAB-003](phase-0/LAB-003-layout-json-and-pdf-extraction.md) | Layout JSON schema and PDF glyph extraction | core | M | CORE-001 | 2 | Ready |
| [SRV-002](phase-0/SRV-002-spike-mls.md) | Spike: MLS for CRDT updates | server | L | SRV-001 | 2 | Ready |
| [CORE-003](phase-0/CORE-003-spike-deterministic-text.md) | Spike: deterministic text pipeline | core | L | CORE-002 | 3 | Ready |
| [LAB-002](phase-0/LAB-002-word-ground-truth-harness.md) | Word ground-truth harness | core | M | LAB-001; reference machine | 3 | Ready (needs owner hardware) |
| [LAB-004](phase-0/LAB-004-metrics-and-report.md) | Comparison metrics and fidelity report | core | M | LAB-003 | 3 | Ready |
| [DESK-002](phase-0/DESK-002-spike-qt-canvas.md) | Spike: Qt Quick canvas, input, accessibility | desktop | L | DESK-001, CORE-007 | 3 | Ready |
| [WEB-002](phase-0/WEB-002-spike-worker-canvas.md) | Spike: worker canvas, input bridge, accessibility mirror | web | L | WEB-001, CORE-007 | 3 | Ready |
| [CORE-008](phase-0/CORE-008-font-audit.md) | Font audit and bundled-library proposal | core + docs | M | CORE-003, LAB-002 | 4 | Ready |
| [LAB-005](phase-0/LAB-005-probes-and-first-study.md) | Probe generator and first Word study | core + docs | L | LAB-002, LAB-003, CORE-003 | 4 | Ready |
| [SRV-003](phase-0/SRV-003-threat-model.md) | Threat model v1 | docs | M | SRV-002, CORE-007 | 4 | Ready |
| [DOCS-002](phase-0/DOCS-002-contributor-onboarding.md) | Contributor onboarding guides | docs | S | Wave-1 scaffolds | 4 | Ready |

## Phase 1 — Faithful Viewer (drafts)

Draft briefs, grouped by stream, to be split into individual Ready briefs at the Phase-0 gate:

| File | Work packages |
|---|---|
| [phase-1/core.md](phase-1/core.md) | CORE-101 … CORE-130 |
| [phase-1/lab.md](phase-1/lab.md) | LAB-101 … LAB-109 |
| [phase-1/desktop.md](phase-1/desktop.md) | DESK-101 … DESK-104 |
| [phase-1/web.md](phase-1/web.md) | WEB-101 … WEB-103 |
| [phase-1/server.md](phase-1/server.md) | SRV-101 … SRV-105 |
| [phase-1/docs.md](phase-1/docs.md) | DOCS-101 … DOCS-103 |
| [phase-1/cross-cutting.md](phase-1/cross-cutting.md) | X-101, X-102 |

## Later phases

Epics for Phases 2–6 are listed in [plan/05-work-breakdown.md](../plan/05-work-breakdown.md#phases-26-epics) and are broken into work packages at each gate review.
