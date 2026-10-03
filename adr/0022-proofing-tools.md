# ADR-0022: Proofing tools — spelling, grammar, hyphenation

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** PRF-01…PRF-05, TYP-04, ADR-0009, ADR-0021, ADR-0024

## Context

Word users expect spelling and grammar checking in many languages, automatic hyphenation, a thesaurus, and custom dictionaries, all private. Facts verified on 2026-10-03: **spellbook** 0.4 (MPL-2.0) reads Hunspell dictionaries in pure Rust (alpha status); **Harper** (harper-core 2.x, Apache-2.0, Automattic) is a fast rule-based grammar checker in Rust for English variants, with WebAssembly support; **hypher** provides TeX hyphenation patterns for 48 languages under permissive licenses. Hunspell dictionaries for many languages exist under varied licenses (LGPL, MPL, GPL, BSD, CC).

## Decision

1. **Spelling:** spellbook in `bayan-proof`, contributing upstream as needed; dictionaries distributed as **separate, downloadable data packs** with per-dictionary license metadata, integrity hashes, and organization mirroring for air-gapped deployments.
2. **Grammar:** Harper for English in Phase 2, running in the engine on desktop and web. Deeper style and context checks come from local AI in Phase 5 (ADR-0024). Other languages via extensions or an organization-hosted grammar server configured by an administrator.
3. **Hyphenation:** hypher patterns for covered languages; additional pattern packs after license review. Hyphenation behavior is measured against Word in the lab; documents relying on Word's proprietary hyphenation dictionaries may differ, and the Fidelity Inspector says so.
4. **Thesaurus:** openly licensed thesaurus data in Phase 4.
5. **Proofing results are annotations**, never document changes, and never sent off the device.
6. **Per-document proofing state** (`w:proofState`, ignored words) and user dictionaries are preserved and synced like other settings.

## Consequences

- Private, fast proofing on every platform with the same results.
- Grammar beyond English is weaker than Word's at first; this is a known gap with a path (AI, extensions).

## Alternatives considered

- **Hunspell (C++):** contrary to ADR-0006.
- **LanguageTool as the default grammar engine:** strong multilingual rules, but a Java server; offered only as an optional organization-hosted service.
- **Platform spell checkers:** inconsistent across platforms and browsers.

## Revisit when

spellbook stalls; Harper adds languages; local AI makes rule-based grammar redundant.
