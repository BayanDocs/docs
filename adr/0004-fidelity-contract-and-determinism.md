# ADR-0004: Fidelity contract and layout determinism

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** FID-01…FID-10, [plan/01 — Fidelity Contract](../plan/01-vision-and-fidelity-contract.md#the-fidelity-contract), ADR-0005, ADR-0009, ADR-0010, ADR-0011, ADR-0025, [specs/fidelity-lab.md](../specs/fidelity-lab.md)

## Context

The specification demands that "the layout is the layout" everywhere and that documents never shift relative to Microsoft Word. These are two different properties. The first (determinism across our own installations) is fully within our control. The second (agreement with Word) depends on reproducing an unpublished algorithm that itself varies across Word versions, platforms and installed fonts. Conflating them would either make the contract untestable or make us promise something no one can deliver.

## Decision

1. **Adopt the four-tier Fidelity Contract** defined in [plan/01](../plan/01-vision-and-fidelity-contract.md#the-fidelity-contract):
   - **Tier A — determinism (guaranteed):** identical layout and reference-raster output on every supported platform for a given version.
   - **Tier B — lossless round-trip (guaranteed):** nothing BayanDocs did not edit is changed on save.
   - **Tier C — Word fidelity (measured and published):** agreement with a pinned build of Microsoft Word for Windows, measured by the Fidelity Lab.
   - **Tier D — reverse fidelity (designed for):** BayanDocs-authored documents look the same in Word.
2. **The determinism chain is owned end to end by the core:** fonts come from content-hashed files (bundled, embedded or organization-provided), shaping and rasterization use our pinned libraries, and layout uses integer arithmetic (ADR-0005). No platform text APIs participate in layout or reference rendering.
3. **Machine-dependent layout is always visible.** If layout depends on a font found only among the user's installed fonts, the document is flagged as machine-dependent, and the user is offered alternatives (embed if the font license permits, use the organization library, or substitute).
4. **Layout epochs.** The engine exposes an integer `layout_epoch`. Any change that alters layout output for any document in the determinism or fidelity corpora either increments the epoch (with a changelog entry) or is rejected. Collaboration sessions require all participants to run the same epoch; clients on another epoch are asked to update before joining.
5. **The reference for Tier C** is Microsoft Word for Windows from the Microsoft 365 Current Channel at a pinned build recorded in the lab manifest, re-baselined deliberately (never silently). Word for Mac and older Word versions are measured as secondary references when the lab has them.
6. **Enforcement:** Tier A by the determinism matrix (ADR-0025); Tier B by round-trip suites and fuzzing; Tier C by the fidelity gate; Tier D by lab runs on BayanDocs-authored documents from Phase 2.

## Consequences

- Fidelity becomes a number that improves release by release, and regressions are caught automatically.
- The engine must avoid every source of nondeterminism, which constrains library choices and coding style (ADR-0005, ADR-0006).
- We must carry fonts ourselves rather than rely on the operating system, which adds download size (mitigated by lazy loading on the web and optional packs on desktop).
- Keeping old layout behaviors alive for pinned documents is **not** promised; layout-epoch pinning for regulated workflows is an open question for Phase 4.

## Alternatives considered

- **Use each platform's native text stack** (DirectWrite, Core Text, FreeType/HarfBuzz via the browser): looks native, but guarantees platform differences. Rejected.
- **Promise pixel identity with Word:** impossible to verify or achieve. Rejected in favor of measured Tier C.
- **Store Word's last layout in the file and replay it:** only works until the first edit, and Word does not store a full layout. We do use Word's `w:lastRenderedPageBreak` hints as a diagnostic.

## Revisit when

A platform or browser forces nondeterminism we cannot route around (for example, a mandatory platform text API), or demand for layout-epoch pinning becomes concrete.
