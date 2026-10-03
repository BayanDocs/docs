# SRV-002: Spike — MLS encryption of CRDT updates, native and WebAssembly

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | CRYPTO / SERVER |
| Repository | bayan-server (`spikes/mls/`); findings feed `bayan-mls` in bayan-core later |
| Attach to session | bayan-server, docs |
| Size | L |
| Depends on | SRV-001 |
| Unblocks | SRV-003, SRV-103, Phase-3 encryption work |
| Status | Ready |
| Requirements | COL-04, COL-05, COL-06, SEC-08 |
| Decisions | ADR-0016 (this spike is its validation gate), ADR-0006, ADR-0015 |
| Specs | [threat-model.md](../../specs/threat-model.md) (T5–T8) |

## Context

ADR-0016 chooses MLS (RFC 9420) via OpenMLS 0.9 with the standard ciphersuite `MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519` at launch, one group per document, handshake messages in public framing so the server can validate membership changes, application messages (CRDT updates) in private framing, and roles in a signed group-context extension. Research on 2026-10-03 found OpenMLS builds for WebAssembly but its upstream CI does not test that build, it had 2026 security advisories, and post-quantum suites exist only with provisional code points. In MLS private framing the sender is encrypted, so the server must enforce write permissions from the authenticated connection (device identity mapped to its member entry), while clients verify the decrypted sender's role.

## Objective

Prove the MLS design end to end natively and in WebAssembly, measure it at realistic group sizes, and confirm or amend ADR-0016.

## Scope

### In scope

- OpenMLS (pinned) with the RustCrypto provider: create a group; publish and fetch key packages; add, remove and update members; process commits and welcomes; send application messages carrying opaque payloads of 100 B to 100 KB (simulating CRDT updates).
- A **server-side validator** component that tracks each group's public state from public-framing handshake messages, validates commits, and enforces role policy on membership changes and on application messages using the authenticated sender device (simulated transport authentication).
- A **role roster** as a custom, signed group-context extension; clients verify the decrypted sender's role before accepting an update.
- **New-member history:** prototype of encrypted snapshots under per-snapshot keys distributed through the group, so a new member can read current state (ADR-0016 §4).
- **Group re-creation** path for ciphersuite migration (create a new group from an old one's membership).
- **WebAssembly:** build and run the client side in Node and headless Chromium.
- **Measurements:** commit and welcome sizes and times at 2, 10, 100 and 1,000 members; encryption throughput; WebAssembly size; storage-provider persistence and what a library upgrade would require.
- **Post-quantum (measurement only):** run the draft hybrid suite behind its feature flag to measure size and time overhead; never as a long-lived configuration.
- **Fallback check:** confirm mls-rs builds for WebAssembly and supports the same flows in principle (time-boxed).
- Report (`spikes/mls/REPORT.md`) and a docs pull request updating ADR-0016's validation status and listing design changes.

### Out of scope

Production server endpoints, identity cross-signing implementation (designed in SRV-003, built in Phase 3).

## Deliverables

Spike code, tests, benchmarks, report, docs pull request.

## Acceptance criteria

- [ ] AC-1 All flows work natively and in WebAssembly (Node and Chromium), with tests.
- [ ] AC-2 The validator rejects unauthorized membership changes and application messages from devices without write roles; clients reject updates whose decrypted sender lacks the role (tests for each).
- [ ] AC-3 Measurements at 2, 10, 100 and 1,000 members are reported, with a judgment on group-per-document scalability.
- [ ] AC-4 The new-member snapshot prototype works and its security properties are described.
- [ ] AC-5 The report recommends library, ciphersuite plan and any ADR-0016 amendments.

## Verification

`cargo xtask verify`; Node and browser test runs; benchmark commands in the report.

## Notes and pitfalls

Never use provisional post-quantum code points for anything persistent; label them clearly in the spike.

## Escalate if

The design needs cryptographic constructions beyond what MLS and its providers offer; that requires expert review (ADR-0016 §12).
