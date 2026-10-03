# 00 — Start Here (for the project owner)

This is the master plan for BayanDocs, written in the first planning session on 2026-10-03. It makes every decision needed to start building, breaks the first phase into work packages you can hand to agents, and sets up the process for planning each later phase. You asked the planner to own the plan; this page tells you what it decided, what you need to do, and how to use the rest.

## The strategy in five sentences

1. **Fidelity first.** We build a faithful `.docx` *viewer* before an editor, because an editor on top of an inaccurate layout engine is wasted work, and we measure fidelity against real Microsoft Word continuously in a Fidelity Lab.
2. **One engine everywhere.** Everything that understands documents lives in one Rust engine compiled for desktop and for the browser, so the layout really is the layout on every platform, and the Qt and React applications stay thin.
3. **Local-first, zero-knowledge.** Editing works fully offline by default; collaboration is added on top through a server that relays only encrypted data it cannot read, using the IETF MLS standard.
4. **Safety over features.** Memory-safe parsing, no automatic macros or external content, a strict supply-chain policy, and lossless round-trips come before any feature.
5. **Rolling-wave planning.** Phase 0 is planned in full detail, Phase 1 in draft, later phases as goals; each phase ends with a gate review that plans the next one from measured evidence.

## What was decided

Every decision has an ADR with its reasoning and alternatives ([adr/README.md](../adr/README.md)). The headline choices:

| Area | Decision |
|---|---|
| Engine | Rust; no C/C++ parsers for untrusted input; integer layout units for cross-platform determinism |
| Document model | Shaped like Word's own internal model (a stream of characters where paragraph marks and field delimiters are characters), so merges behave the way Word users expect |
| Collaboration data | Loro CRDT behind an adapter (Automerge 3 as fallback), validated by a spike before commitment |
| Text | harfrust shaping, skrifa fonts, ICU4X segmentation, our own Word-compatible line breaking and measurement model |
| Fonts | Bundled metric-compatible open fonts, embedded fonts, organization font library, and a programme to fill gaps such as Aptos |
| Rendering | Our own display lists and a deterministic CPU rasterizer; PDF via krilla (PDF/X built by us) |
| Engine boundary | A small JSON message protocol over a C ABI (desktop) and a Web Worker (web), with record/replay |
| Desktop | Qt 6.12 LTS with Qt Quick, C++20 as glue only, LGPL modules only |
| Web | React + TypeScript + Vite, engine in a Web Worker, pnpm with the 24-hour release-age rule enforced natively |
| Server | Rust (tokio/axum), one container, SQLite by default, PostgreSQL and S3 optional |
| Encryption | MLS (RFC 9420) via OpenMLS; standard ciphersuite now, hybrid post-quantum when standardized |
| Supply chain | Your dependency preferences, encoded as ADR-0017 and enforced in CI in every repository |
| Licensing (needs your confirmation) | MPL-2.0 for core, desktop and web; AGPL-3.0-or-later for the server; CC BY 4.0 for documentation; DCO sign-off, no CLA |

## Where the plan sharpened the original specification

Nothing was scaled back, but some items were made precise so they can be tested (details in [01-vision-and-fidelity-contract.md](01-vision-and-fidelity-contract.md)):

- `.docx` is zipped XML, not a binary format; the binary format is legacy `.doc`, which we also support.
- "Never shift a single pixel" became a four-tier Fidelity Contract: guaranteed determinism between BayanDocs installations, guaranteed lossless round-trips, measured and published fidelity against Word, and designed-in fidelity when Word opens our files. An absolute pixel guarantee against Word is impossible for anyone, because Word's algorithm is unpublished and Word differs between its own versions.
- PDF/A is for archives; print houses want PDF/X. We deliver both, plus accessible PDF/UA.
- Running arbitrary VBA "instantly" is not achievable; macros are preserved, inspectable, assisted-translatable to JavaScript, and later runnable in a sandbox for a documented subset.
- The plan adds what "as good as Word in every way" silently requires: accessibility, right-to-left and East Asian typography, proofing, legacy formats, references, review tools, mail merge, forms and reliability.

## What you need to do

The full list is [09-owner-checklist.md](09-owner-checklist.md). The first four:

1. **Fix the default branch** in all five repositories (they were empty, so the planning branch became the default).
2. **Confirm or change the licensing decision** in [ADR-0003](../adr/0003-licensing-and-contribution-model.md).
3. **Turn on security alerts (not update bots), secret scanning and Actions hardening** in each repository's settings.
4. **Plan the Word reference machine** (Windows + Microsoft 365) for the Fidelity Lab; it is needed in about the third wave of Phase 0.

## How to start handing off work

1. Open [workpackages/README.md](../workpackages/README.md). Wave 1 has six independent work packages; good first picks are CORE-001, SRV-001 and WEB-001.
2. Follow the hand-off procedure and paste the prompt from [06-agent-workflow.md](06-agent-workflow.md#work-package-session).
3. Review each pull request with a separate reviewer session ([prompt](06-agent-workflow.md#pull-request-review-session)) and merge when CI is green and the reviewer approves.
4. Run three to five work packages at a time so you can keep up with reviews.

## Reading order

| If you have… | Read |
|---|---|
| 15 minutes | This page and [04-roadmap.md](04-roadmap.md) |
| An hour | Add [01-vision-and-fidelity-contract.md](01-vision-and-fidelity-contract.md), [03-architecture.md](03-architecture.md), [06-agent-workflow.md](06-agent-workflow.md) |
| An afternoon | Add [02-requirements.md](02-requirements.md), the ADR index and a few ADRs, [08-risk-register.md](08-risk-register.md), [10-learning-path.md](10-learning-path.md) |

## Honest expectations

This is a multi-year project: a useful viewer in roughly the first year, a daily-driver editor in the second, and 1.0 in roughly three to five years, re-estimated at every gate from real throughput. The hardest part is not writing code but discovering exactly how Word lays out text, which is empirical research. The single largest fidelity risk is fonts, above all Aptos (Word's default since 2023–2024), which has no open metric-compatible equivalent yet. The plan addresses both head-on, and the Fidelity Lab will tell us, with numbers, how we are doing.
