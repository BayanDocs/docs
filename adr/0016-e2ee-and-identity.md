# ADR-0016: End-to-end encryption and identity with MLS

- **Status:** Accepted — validation gate (SRV-002), met on 2026-10-07 (see the proposed amendment of that date); external review required before collaboration GA
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

## Amendment 2026-10-07: results of the SRV-002 validation gate (proposed)

Proposed on 2026-10-07 by work package SRV-002 ([BayanDocs/bayan-server pull request 5](https://github.com/BayanDocs/bayan-server/pull/5)); the spike's full report is `spikes/mls/REPORT.md` in bayan-server. **Not binding until the owner accepts it.**

**Validation result.** SRV-002 met the validation gate above with OpenMLS 0.9.0 and its RustCrypto provider (`openmls_rust_crypto` 0.6.0), natively and in WebAssembly (in Node.js 24 and in headless Chromium 153): creating groups, publishing and fetching key packages, adding, removing and re-keying members, joining from Welcomes, encrypting and decrypting update payloads of 100 B to 100 KB, a server-side validator that follows each group's public state from commits in public framing and enforces the role policy without holding any key, clients that check every decrypted sender's role, encrypted snapshots for newcomers, moving a group to another ciphersuite, saving and loading a device's state, and measurements at 2, 10, 100 and 1,000 members with the classical suite and with the hybrid post-quantum suite. The same 53 tests pass on all three platforms. Decision 1 (OpenMLS, with mls-rs as the fallback) and Decision 3 (one group per document, commits in public framing, updates in private framing) stand. mls-rs 0.56 runs the same flows natively and in WebAssembly, but only with classical suites: its post-quantum suites need its AWS-LC provider, which is C code (ADR-0006) and does not build for WebAssembly, so it remains a fallback for the classical suite only.

**The post-quantum plan (amendment of 2026-10-04) needs no change.** OpenMLS 0.9.0 already implements the hybrid suite that amendment names (ML-KEM-768 + X25519 with AES-128-GCM, SHA-256 and Ed25519) in pure Rust, behind its draft feature flag and under the provisional code point `0x004F`. It builds for WebAssembly and every flow works with it. The spike used it only behind a feature flag, labeled as provisional, and refused to save anything made with it, groups and key packages alike. Compared with the classical suite it leaves updates and signatures unchanged, makes key packages about 8.5 times larger (2.6 KiB), adds about 1.1 KiB to every public-key encryption in commits and Welcomes, makes commits take two to three times as long to create and three to six times as long to process and validate, and makes device and server state 6 to 7 times larger.

**Design details settled by the spike.** They make Decisions 2 to 5 precise; none needs cryptography beyond MLS and its providers (Decision 12).

1. *Welcomes (Decision 3).* Welcomes carry no ratchet tree. The server keeps every group's public tree anyway, to validate commits, and gives it to newcomers, who check it against the tree hash in the Welcome's signed group information and refuse a tree that does not match.
2. *Snapshots (Decision 4).* A member who may edit encrypts a snapshot of the current document under a fresh random key with the group's AEAD, through the MLS crypto provider, with the group ID and a random snapshot ID as associated data. The server stores the encrypted blob. The key, the snapshot ID and the SHA-256 hash of the blob travel to the group in an MLS application message. A newcomer checks that the sender's role allows editing and that the blob's hash matches before decrypting it. By default a snapshot holds the current state without edit history (threat T10). The construction and the security properties in the report go to the external review (SEC-08), together with the migration announcement of detail 4.
3. *Roles (Decision 5).* Roles belong to users, not devices, and live in a private-use group-context extension that every member's capabilities must list. "Signed" means MLS's own authentication of the group context: the roster is covered by the signature on every group information message, bound into the key schedule, and changes only through a commit that its sender signs; no additional signature is used. Only owners add or remove other users' devices, change roles, or change anything else in the group context, even with a commit that keeps the roster as it is; a user's devices may add and remove each other; every commit must leave exactly one role for each user who has a device in the group, no role for anyone else, and at least one owner. The group context always holds exactly two extensions, the roster and the required-capabilities extension that requires the roster's type and basic credentials: no external senders (keys with which someone outside the group could propose changes) and nothing else. The server checks all of this on every commit before relaying it and when a group is registered, and clients check it again before applying a commit or accepting a Welcome. An update's sender and content are encrypted, so the server accepts updates only over connections of devices whose user may send updates at all (owner, editor or commenter) and refuses viewers; clients enforce the difference between edits and comments after decrypting, judge a late update by the roles of the epoch it was sent in as well as the current one, and discard any update the sender's role does not allow.
4. *Ciphersuite migration (Decision 2).* OpenMLS 0.9 does not implement MLS's re-initialization (`ReInit` proposals with a resumption pre-shared key, RFC 9420 §11.2). Until it does, an owner moves a document by creating a new group with the same members and roles from fresh key packages, and announcing the move in the old group with an update that only owners may send; every member checks that the new group has exactly the old group's members and roles and the announced ciphersuite before switching.
5. *Scale (Decision 3).* One group per document is designed for documents of up to a few hundred members, with 1,000 as a supported upper bound that needs the mitigations in the report. In a 1,000-member group with the hybrid suite, a member's first commit after many members were added at once (as moving a document produces) can reach 1.1 MiB, and a device keeps about 9.5 MiB of state for that document. Very large read-only audiences need a design that does not make every viewer an MLS member, to be settled in Phase 3 together with link sharing (Decision 8).

**Requirements for `bayan-mls` and the server.**

1. Joining from a Welcome is one storage transaction. OpenMLS deletes the key package's private keys before it has validated the rest of the Welcome, so a failed join must be rolled back; otherwise a server could make a newcomer's Welcome unusable by sending a bad tree.
2. OpenMLS's stored state can change format between versions without any version signal: from 0.8.1 to 0.9.0 the stored numbers of GREASE values and custom extension, credential and proposal types changed for compact binary encodings, while OpenMLS's storage version number stayed the same (JSON storage was unaffected, and a state saved by 0.8.1 kept working in 0.9.0). `bayan-mls` versions its own stored data, keeps stored fixtures from every released version, tests loading them in CI, and upgrades OpenMLS only together with a migration step whenever those fixtures show one is needed.
3. Devices keep at most one past epoch's keys: OpenMLS 0.9 rewrites the members of every kept epoch with each update, so at 1,000 hybrid members each kept epoch adds about 25 ms to every update in the browser and 4.4 MiB to the stored state.
4. Stored state uses a compact binary encoding, and on the web an IndexedDB storage provider; both are encrypted at rest (SEC-11). OpenMLS ships only an in-memory provider that stores JSON text and one for SQLite.
5. The members and roles of each epoch are cached, not rebuilt for every update.
6. A recovery design for commits that the server accepts but the members refuse (see Consequences), chosen in SRV-003 and built by SRV-103 and `bayan-mls`.

**Consequences.** The external audit before collaboration leaves beta (Decision 12, SEC-08) also covers the young post-quantum crates OpenMLS uses (RustCrypto's `ml-kem` 0.3 and `x-wing` 0.1), for which no third-party audit was found. The threat model (SRV-003) records what the validator's design lets the server see and do: each group's members and their roles, who commits and when, and the sizes and timing of updates and snapshots; it can withhold, delay or reorder messages and split a group, but cannot read, forge or alter them.

Members, not only the server, can split or stall a group. The server cannot check the parts of a commit that are keyed with the epoch's secrets (its membership and confirmation tags, and the path secrets it encrypts to the other members), so any member, a viewer included, can send a commit that the server accepts and every other member refuses. The server then follows the group into an epoch the members never reach and refuses all their later commits, including the owner's removal of that member; nothing is read or forged, but the group can no longer change. The spike documents and tests this limitation without a fix. SRV-003 chooses the recovery design (requirement 6). The spike's report weighs three options that need no cryptography beyond MLS: two-phase acceptance at the server, which keeps the previous epoch's public state until a device of another user confirms the new epoch and otherwise drops the commit and quarantines its sender (recommended); MLS's resync external commits, by which each stuck member rejoins at the server's epoch; and an owner's move to a new group that may leave users out.
