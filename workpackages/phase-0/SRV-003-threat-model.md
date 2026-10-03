# SRV-003: Threat model v1 — server, sync and encryption

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | SECURITY / CRYPTO |
| Repository | docs (references bayan-server and bayan-core) |
| Attach to session | docs, bayan-server, bayan-core |
| Size | M |
| Depends on | SRV-002, CORE-007 |
| Unblocks | SRV-101…SRV-105 refinement at the Phase-0 gate |
| Status | Ready |
| Requirements | SEC-12, COL-04…COL-06, COL-10 |
| Decisions | ADR-0015, ADR-0016, ADR-0023 |
| Specs | [threat-model.md](../../specs/threat-model.md) |

## Context

The v0 threat model lists assets, adversaries, trust boundaries and principal threats, and ends with open items (§6). With the MLS spike's findings and the engine boundary in place, the model can now be made concrete enough to shape the Phase-1 server work packages.

## Objective

Threat model v1 with data-flow diagrams, per-element analysis, a metadata inventory and endpoint-level security requirements, plus recommended changes to Phase-1 server work packages and ADRs.

## Scope

### In scope

- Data-flow diagrams (Mermaid) for: login (OIDC and passkeys), device enrollment and cross-signing, sharing and role changes, E2EE link sharing, sync (online and offline), snapshot creation and new-member onboarding, recovery (recovery kit and passkey PRF), device loss and revocation.
- STRIDE analysis per element and flow, with mitigations and residual risks.
- A field-by-field inventory of metadata the server stores and sees, with justification and retention.
- Role-enforcement design details and the failure modes when server and clients disagree.
- Compliance escrow member design and its abuse cases.
- A security requirements checklist per planned server endpoint.
- Recommendations: changes to `workpackages/phase-1/server.md`, and ADR amendments if needed (as Proposed ADRs).

### Out of scope

Implementation.

## Deliverables

`specs/threat-model.md` v1, updated Phase-1 server drafts, any Proposed ADRs.

## Acceptance criteria

- [ ] AC-1 Every open item in v0 §6 is addressed.
- [ ] AC-2 Every flow has a diagram and a STRIDE table.
- [ ] AC-3 The metadata inventory lists every field with purpose and retention.
- [ ] AC-4 A separate reviewer session has reviewed the model (link in the pull request).

## Verification

Docs verify script (after DOCS-001); reviewer session.

## Escalate if

The analysis finds a flaw in ADR-0016's design; write it up as a Proposed ADR and flag it to the owner.
