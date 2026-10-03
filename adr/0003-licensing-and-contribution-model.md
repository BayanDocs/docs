# ADR-0003: Licensing and contribution model

- **Status:** Proposed — owner confirmation required (ADR-0001 §5)
- **Date:** 2026-10-03
- **Deciders:** Planner (proposal); owner (confirmation)
- **Related:** X-001, ADR-0017 (license allowlist), [plan/09-owner-checklist.md](../plan/09-owner-checklist.md)

## Context

The owner wants BayanDocs "completely free and open source". Licensing is the hardest decision to change later: once outside contributors hold copyright in their contributions, relicensing requires every one of them to agree. The choice must also be compatible with Qt (LGPLv3 for the modules we use), with fonts (mostly SIL OFL 1.1) and with our dependencies (mostly MIT, Apache-2.0, BSD).

Forces:

- **Adoption and embedding:** a reusable `.docx` layout engine has value beyond BayanDocs (converters, viewers, other editors). A license that allows embedding spreads the fidelity work and attracts contributors.
- **Keeping improvements open:** modifications to BayanDocs itself should stay open.
- **Network use:** a collaboration server can be run as a closed SaaS fork without ever "distributing" it; only the AGPL closes that gap.
- **Precedent:** LibreOffice uses MPL-2.0 for its code; self-hosted collaboration servers such as Nextcloud, CryptPad and the OnlyOffice document server use AGPL-3.0.

## Decision (proposed)

| Repository / artifact | License |
|---|---|
| bayan-core | **MPL-2.0** |
| bayan-desktop | **MPL-2.0** |
| bayan-web | **MPL-2.0** |
| bayan-server | **AGPL-3.0-or-later** |
| docs (prose, diagrams) | **CC BY 4.0**; code snippets in docs additionally under **MIT-0** so they can be copied freely |
| Fonts created by the project | **SIL OFL 1.1** |

- **Contributions:** inbound = outbound under each repository's license, certified by the **Developer Certificate of Origin** (`Signed-off-by` on every commit). **No contributor license agreement.** This deliberately means the project cannot later be relicensed to a proprietary license.
- **AI-assisted contributions:** the DCO is a certification only a person can make. Commits authored by AI agents carry the agent's attribution trailers and are **not** signed off by the agent. The human who submits or merges the work (initially the owner) certifies the DCO for them, by a sign-off line in the pull request description and in the squash-merge commit. Human-authored commits are signed off by their human author as usual. X-001 implements the DCO check accordingly.
- **REUSE compliance:** every file carries SPDX license and copyright headers, checked in CI.
- **Trademark:** the name and logo are governed by a separate trademark policy (drafted before the first public release), so forks must rename while the code stays free.

### Compatibility notes

- MPL-2.0 code may be combined into an AGPL-3.0 work (MPL-2.0 lists the AGPL as a "Secondary License"), so the server can depend on core crates.
- Qt modules used are LGPLv3; the desktop app links them dynamically, which satisfies the LGPL's relinking requirement. GPL-only Qt modules are prohibited (ADR-0013).
- GPL-only libraries cannot be linked into MPL-2.0 repositories without making the combined work GPL; they are therefore excluded by the license allowlist (ADR-0017), except as separately distributed data packs or separate processes where the license permits aggregation.

## Consequences

- Anyone can embed the engine in other software, including proprietary software, but changes to BayanDocs files stay open (MPL's file-level copyleft).
- Hosted forks of the server must share their modifications with their users (AGPL).
- Some enterprises restrict AGPL software; running an unmodified server is usually acceptable under such policies, but this may cost some adoption.
- No future relicensing; this is a trust feature.

## Alternatives considered

- **Apache-2.0 everywhere:** maximum adoption and a patent grant, but allows closed forks of the whole product, including a closed hosted service.
- **GPL-3.0 for the applications:** stronger copyleft, but blocks embedding the engine in non-GPL software and complicates some app stores.
- **AGPL-3.0 everywhere:** strongest protection, but discourages embedding the engine and some contributors.
- **Dual licensing with a CLA:** enables selling commercial licenses but requires contributors to trust a single owner with relicensing power; rejected as contrary to the project's "open all the way down" principle.

## Revisit when

The owner rejects or modifies this proposal. After confirmation and the first external contribution, this decision is effectively permanent.
