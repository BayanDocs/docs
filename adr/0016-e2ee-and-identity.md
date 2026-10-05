# ADR-0016: End-to-end encryption and identity with MLS

- **Status:** Accepted — validation gate (SRV-002); external review required before collaboration GA
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** COL-04…COL-06, COL-09, COL-10, SEC-08, SEC-11, ADR-0008, ADR-0015, [specs/threat-model.md](../specs/threat-model.md), SRV-002, SRV-003

## Context

Collaboration must be zero-knowledge: document content, titles, comments, media, history and folder structure are encrypted on the user's device. Groups change over time (sharing, revocation, new devices), so we need efficient group key agreement with forward secrecy and post-compromise security. The IETF standard for this is **Messaging Layer Security** (MLS, RFC 9420; architecture in RFC 9750). Facts verified on 2026-10-03:

- **OpenMLS** 0.9.0 (MIT; Phoenix R&D and Cryspen spin-off CE Labs) builds for WebAssembly; its RustCrypto provider supports the standard ciphersuites and, behind a feature flag, draft post-quantum suites with provisional code points. It had security advisories in 2026 and a storage-format regression in 0.8.x; no public third-party audit was found.
- **mls-rs** 0.56 (Apache-2.0/MIT, AWS Labs) builds for WebAssembly; its post-quantum support is native-only with private code points; it reports no full third-party audit.
- The IETF draft for post-quantum MLS ciphersuites entered Working Group Last Call on 2026-10-01; **code points are not yet assigned.** Its first hybrid suite is ML-KEM-768 + X25519 (X-Wing) with AES-128-GCM, SHA-256 and Ed25519.
- The WebAuthn PRF extension (deriving keys from passkeys) works in current Chrome, Edge, Safari and Firefox, and on Windows Hello only since February 2026; password-manager support is uneven.
- Web code integrity: the WAICT effort (Cloudflare, Mozilla, Meta, Freedom of the Press Foundation) has a Firefox Nightly prototype but has not shipped; the `Integrity-Policy` header (enforced Subresource Integrity) is available in all major browsers.
- Prior art: an academic design for E2EE collaborative documents (USENIX Security 2026) uses an encrypted group broadcast channel (MLS or Signal-style) plus a CRDT, which is our architecture. CryptPad uses fixed per-document keys (no forward secrecy); Proton Docs encrypts Yjs updates.

## Decision

1. **MLS via OpenMLS**, used through the `bayan-mls` crate (in core, shared with the server for validation). **mls-rs** is the fallback behind the same interface.
2. **Ciphersuite:** `MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519` (0x0001) on every platform at launch. When IANA assigns code points for the hybrid post-quantum suite (ML-KEM-768 + X25519), new groups use it and existing documents migrate by re-keying into new groups. **Provisional code points are never used for long-lived groups.** Crypto agility is achieved by group re-creation, which the protocol supports from day one.
3. **One MLS group per document** (and per shared folder index). Document updates are MLS application messages (private framing). Membership changes are handshake messages in public framing so the server can validate them and enforce role policy.
4. **Readable history for new members:** MLS forward secrecy means new members cannot decrypt earlier epochs. Clients therefore produce **encrypted snapshots** of document state under per-snapshot keys and share those keys with new members through the group, so a newcomer receives the current state plus whatever history the sharer chooses to include.
5. **Roles** (owner, editor, commenter, viewer) are stored in a signed group-context extension. The server rejects writes from members without write roles; clients independently verify every update's sender role and discard unauthorized updates, so a misbehaving server cannot grant write access.
6. **Identity and devices:** each user has a long-term identity key that cross-signs device keys; MLS credentials bind device signature keys to the user identity, and clients verify the chain. Users can verify each other with safety numbers or QR codes; key transparency is a later enhancement. The server cannot silently add devices to a user.
7. **Recovery:** a recovery kit (a high-entropy key the user saves or prints) is always available. Passkey PRF unlock is an optional convenience, never the only path.
8. **Link sharing:** the link secret travels in the URL fragment (never sent to the server) and unwraps a read capability; detailed design in Phase 3.
9. **Metadata minimization:** titles, folder structure and comments are encrypted; the server sees membership, sizes and timing, and the threat model states this residual leakage.
10. **Compliance for organizations (Phase 4):** an organization-controlled escrow member may be added to groups by policy, with its key held by the organization; the server remains zero-knowledge.
11. **Web client trust:** the desktop app is the highest-assurance client. The web app ships with Subresource Integrity enforced by `Integrity-Policy`, reproducible builds with published hashes, and will adopt web-app transparency standards (such as WAICT) when browsers ship them.
12. **No custom cryptography.** Any primitive not provided by MLS or its providers requires an ADR and expert review. An external audit of the protocol design and implementation is required before collaboration leaves beta.

## Consequences

- A standards-based design that auditors and cryptographers recognize.
- Server-side search, previews and content in notifications are impossible; clients index locally, render previews locally and receive content-free notifications.
- Group re-creation for algorithm migration must be a well-tested path.

## Alternatives considered

- **Fixed per-document symmetric keys (CryptPad-style):** simple, but no forward secrecy or post-compromise security, and revocation requires re-encrypting everything.
- **Signal-style pairwise sender keys (Megolm):** proven, but scales worse for membership changes than MLS.
- **Keyhive/BeeKEM (Ink & Switch):** promising local-first access control, but explicitly pre-alpha and unaudited.
- **mls-rs as primary:** viable; OpenMLS chosen for its WebAssembly-capable post-quantum path and broader community.

## Validation gate

SRV-002 must demonstrate, natively and in WebAssembly: group creation, adding and removing members, updates, encryption and decryption of CRDT update payloads, public-framing validation of commits by a server component, and performance at 2, 10, 100 and 1,000 members, with a recommendation on library and ciphersuite plan.

## Revisit when

IANA assigns post-quantum MLS code points; an OpenMLS or mls-rs audit is published; WAICT or similar ships in browsers; the external audit recommends changes.

## Amendment 2026-10-04: post-quantum encryption from the first release

Decided by the owner on 2026-10-04 during SRV-001 ([BayanDocs/bayan-server pull request 1](https://github.com/BayanDocs/bayan-server/pull/1)), after discussing "harvest now, decrypt later" (threat T22 in the [threat model](../specs/threat-model.md)): an adversary, including a hostile server operator who keeps every encrypted message, can store MLS ciphertext today and decrypt it once a large quantum computer can break X25519. Re-keying into a new group later protects only what is sent afterwards.

This amendment replaces the first sentence of Decision 2:

- **Collaboration ships with the hybrid post-quantum ciphersuite from its first release, beta and GA alike.** No real user's document is ever protected only by a classical key exchange. The suite is the first one IANA assigns from the IETF draft for post-quantum MLS ciphersuites (draft-ietf-mls-pq-ciphersuites, in Working Group Last Call since 2026-10-01): as the context above notes, ML-KEM-768 + X25519 (X-Wing) with AES-128-GCM, SHA-256 and Ed25519. Collaboration is planned for Phase 3, so the code point is expected well before then.
- **Until the code point is assigned,** the classical suite `MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519` (0x0001) is used only in development and tests, never for real users' documents. Provisional code points remain forbidden for persistent groups (Decision 2).
- **If the code point is still unassigned at the Phase-3 gate,** that gate decides between delaying the collaboration beta and launching with the classical suite, a clear warning to users and the planned re-keying migration, accepting that whatever is shared before the migration stays exposed to harvest-now-decrypt-later.
- **Later decisions, not made now:** post-quantum signatures (signatures are not exposed to harvest-now-decrypt-later, so migration by group re-creation, Decision 2, covers them), and a higher-assurance suite (for example ML-KEM-1024 with AES-256, which the NSA's CNSA 2.0 requires for US national security systems) if such customers become a target.

SRV-002 already measures the hybrid suite's size and time cost natively and in WebAssembly; its ciphersuite recommendation (AC-5) must show how the plan meets this amendment.
