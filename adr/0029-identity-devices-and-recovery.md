# ADR-0029: Identity keys, device approval and account recovery

- **Status:** Accepted (owner, 2026-10-17) — validation gate (the Phase-3 work package that builds identity and recovery, below). The owner decided against the expert review of its constructions before Phase 3 that the proposal made a condition; the external audit of the cryptographic design before collaboration leaves beta reviews them (ADR-0016 Decision 12, SEC-08).
- **Date:** 2026-10-14 (proposed); 2026-10-17 (accepted, without the expert review before Phase 3)
- **Deciders:** Owner, on 2026-10-17, answering the open questions of SRV-003's [pull request](https://github.com/BayanDocs/docs/pull/42), on the recommendation of the SRV-003 implementer session (ADR-0001 Decision 5: it changes a security design)
- **Related:** COL-05, COL-06, COL-13, SEC-08, SEC-11, SEC-13, OPS-09, [ADR-0012](0012-engine-boundary.md), [ADR-0015](0015-server-architecture.md), [ADR-0016](0016-e2ee-and-identity.md), [ADR-0028](0028-server-tls.md), [ADR-0030](0030-commit-acceptance-and-group-repair.md), [threat model v1](../specs/threat-model.md) (§5, flows F3, F5, F9, F10, F11; threats T11, T23, T24, T27–T30, T39), SRV-002, SRV-003, SRV-101, SRV-103

## Context

ADR-0016 decides the principles of identity and recovery:

- each user has a long-term identity key that cross-signs device keys;
- MLS credentials bind device signature keys to the user's identity, and clients verify the chain;
- users can compare safety numbers or QR codes, and key transparency comes later;
- the server cannot silently add devices to a user (Decision 6);
- a recovery kit is always available, and passkey PRF unlock is an optional convenience, never the only path (Decision 7).

The MLS spike SRV-002 named devices with plain `user/device` credentials and left cross-signing to SRV-003 ("designed in SRV-003, built in Phase 3").

The threat model v1 analyses device enrollment, recovery and device loss, and finds five problems that the principles alone leave open:

1. **No way back into one's documents.** The role policy of ADR-0016's amendment of 2026-10-07 (design detail 3) and the SRV-002 validator accept commits only from members, and a regular MLS commit cannot remove its own committer (RFC 9420 §12.2). A user who loses every device therefore has no device left in any group. Only owners can add the user's new device, and if the user was a document's only owner, nobody can. Worse, that document's membership can never change again: every commit must leave each user who has a device in the group a role and at least one owner, so the lost owner's devices can never be removed. A recovery kit that brings back the identity key but not the documents falls short of Decision 7.
2. **Documents only the user held have no other copy.** MLS's forward secrecy means a new device cannot read earlier epochs, and in a document that only the user's own devices belong to, nobody else can send the new device a snapshot.
3. **Approving a device must be authenticated in both directions.** If an approving device sees only "a device is waiting for approval", the server can register a device of its own at the same moment and have the user approve it. In the other direction, HPKE in the base mode MLS uses does not authenticate the sender: anyone can seal a message to the new device's public key. The server could therefore hand the new device an identity key and a key-backup key of its own.
4. **First contact trusts the directory.** Cross-signing stops the server from adding a device to an identity that a client has already pinned or verified. When a client looks someone up for the first time, though, the server can answer with an identity of its own (a "ghost user"). ADR-0016's sentence "The server cannot silently add devices to a user" therefore holds only for identities a client already knows.
5. **Web devices make web-code risk last.** The web app's code comes from the server each time it loads (threat T11). If a browser device held a key that certifies devices, code served once could copy it and keep certifying the server's own devices for that user long after the user stopped using the browser.

Facts verified on 2026-10-14:

- **External commits in MLS.** RFC 9420 §12.4.3.2 lets a joiner use an external commit to "resync", replacing "a member's prior appearance with a new one". §12.2 allows such a commit at most one Remove proposal, with which the joiner removes an old version of itself; the application must check that the joiner's credential is acceptable for the member it removes.
- **External commits in OpenMLS.** OpenMLS 0.9.0, the pinned version, builds external commits (`ExternalCommitBuilder`), always in public framing, so the server's validator can check them. It adds a Remove only for the member whose signature key equals the joiner's own (`external_commits.rs`), so a new device with a new key can join but cannot, in the same commit, remove another device.
- **Passkeys in apps.** Apple's documentation ("Supporting passkeys") requires an app to have an associated domain for a relying party before it can use passkeys for it. On Apple's platforms, a desktop app therefore cannot use the platform's passkey interface for an arbitrary self-hosted server's domain; the system browser can.
- **Key transparency.** The IETF's key transparency protocol is still an Internet-Draft (draft-ietf-keytrans-protocol-04, April 2026).
- **WebAuthn PRF.** The extension is available in current browsers, and on Windows Hello since February 2026 (ADR-0016, context of 2026-10-03).

## Decision

1. **Three signing keys per account, all Ed25519** (threat model §5.1):
   - The **identity key** says who the user is. Its private part is kept only in the account's secret store (item 6) and, briefly, in the memory of a device that uses it; it is used rarely: to certify a device-signing key when the account is created, after a device loss, and in a recovery.
   - The **device-signing key** says which devices belong to the user and signs the user's device list. The identity key certifies it. The user's **native (desktop) devices** hold it, wrapped at rest with a keychain-protected key (SEC-11), so that any of them can approve a new device (COL-13). **Browser devices never hold it.** A user without a native device approves new devices with the recovery kit (item 8). This refines ADR-0016 Decision 6: the identity key "cross-signs" device keys through this one intermediate key, so that a lost native device costs a rotation of the device-signing key, which contacts see as a change of devices, not a change of identity.
   - Each **device key** is the device's MLS signature key, certified by the device-signing key. Under a separate signing label it also proves the device to the server on every connection and security-relevant request, as DPoP (RFC 9449) does for OAuth tokens.
2. **Credentials carry the chain.** Every MLS leaf's credential names the account and the device and carries the device certificate, the device-signing key's certificate and the identity public key. A chain is valid when it leads to the account's identity key and names a device that the account's latest signed device list lists as current; a certificate made by an earlier device-signing key stays valid for a device that the latest list still lists, and devices replace it with their next self-update in each group. The server's validator and every client check the chain wherever a leaf appears: in key packages, commits, Welcomes, resyncs and recovery joins. The Phase-3 work package chooses the encoding (a private-use MLS credential type or X.509) and specifies the byte formats and signing labels. The group context's required-capabilities extension then requires that credential type instead of basic credentials.
3. **The directory and trust in contacts.**
   - The server publishes, per account, the identity public key, the current device-signing certificate and a signed device list with a version number, the current devices, the revoked ones, and which device made each change.
   - Clients pin a contact's identity key the first time they see it and refuse a device list older than one they have seen. They stop with a warning before sending anything new to a contact whose identity key has changed. Users can compare safety numbers or scan QR codes and then see the contact as verified.
   - Every device of a user shows each change of the user's device list. A device that finds a change attributed to itself that it did not make raises an alarm and starts the response of item 11.
   - A user's document index and settings, which hold pins, verifications and device names, are end-to-end encrypted groups of the user's own devices, so a new or recovered device inherits them.
   - The server can still answer a lookup for someone a client has never seen with an identity of its own. This is stated as a residual risk (threat T23), and key transparency is evaluated at the Phase-3 gate.
4. **Devices are approved by an exchange authenticated out of band.**
   - A new device registers as pending after signing in. Until it is approved it cannot read group data, claim key packages, publish, end other sessions or delete anything.
   - The approving native device and the new device first authenticate each other out of band. Either the approving device scans a QR code that the new device shows, holding the fingerprint of the new device's keys and a one-time secret; or both devices show the same short code from a commit-then-reveal exchange between them.
   - The approving device then sends the approval: the new device's certificate, the new device list, the identity key and the key-backup public key, plus the device-signing key if the new device is native. It seals the approval with HPKE using the hybrid post-quantum KEM to the new device's one-time transfer key, and authenticates it with an AEAD key derived with HKDF from the out-of-band secret.
   - The new device accepts its user's identity key and key-backup key only from that authenticated approval. A bare "Approve?" button is never offered.
   - Administrators can additionally require their own approval (COL-13); that is a gate on the server, not a certificate.
   - Sessions belong to devices, and the device key's proof of possession (item 1) makes a stolen session token useless on its own.
5. **The recovery kit is a generated secret.** The account's first device generates a random 256-bit recovery secret, shows it as words and a QR code, asks the user to confirm part of it, and never stores it. It is never a passphrase chosen by the user: a passphrase would need a password-hashing function such as Argon2id, which MLS's providers do not include (ADR-0016 Decision 12).
6. **The secret store.** A key derived from the recovery secret with HKDF seals the identity key, the device-signing key and the key-backup key with an AEAD under a 256-bit key, bound to the account. The server keeps only the current ciphertext and its version, and a device may read it during a recovery.
7. **The key backup.** Every device that receives a document's snapshot key seals it to its own account's key-backup public key, with HPKE using the production ciphersuite's hybrid post-quantum KEM, and stores it on the server. A recovered device can then read the latest snapshot of every document, including documents nobody else holds. Editors' clients make snapshots at a regular cadence, because a recovery restores only the latest one. The server learns only that a backup entry exists for a group.
8. **Resyncs and recovery joins.** This changes design detail 3 of ADR-0016's amendment of 2026-10-07 in its second point; the first is the credential type of item 2.
   - A **resync** is an MLS external commit by which a device rejoins a group with its own device key and replaces its own old leaf (RFC 9420 §12.4.3.2). It is for a device that fell behind the server's log retention or could not follow a commit.
   - A **recovery join** is an MLS external commit that adds a new approved device of a user who has a role in the group and removes no one. The new device then removes the user's lost devices with ordinary own-device removals, because OpenMLS 0.9.0 cannot do both in one external commit.
   - For both: the device's credential must chain to the user's identity key and appear in the latest signed device list, and the roster must not change. The server's validator and every client check this. The server alone also checks that the session signed in within the last few minutes, since clients cannot.
   - The user's own other devices, which know every revocation, refuse a join by a revoked device. Clients show members that the user rejoined after a recovery.
   - A join by a user who is not an owner takes effect only after a witness confirms it (ADR-0030).
   - Members publish, with each commit, the group information that external commits need, and witnesses check it.
9. **Passkey unlock is opt-in.**
   - A user may wrap a copy of the recovery secret with a key derived (HKDF) from a passkey's PRF output, bound to the credential ID and the account. Switching it on needs the recovery kit once, and administrators can switch the feature off for their organization.
   - The desktop app uses the platform's passkey interface where the platform allows it for the server's domain, and the browser otherwise.
   - The app tells the user that with passkey unlock, whoever can use the passkey, including through its sync provider, can both sign in and unlock the account. It also tells them that in a browser the server's code sees the unlocked secret (threat T11).
   - It is never the only path (ADR-0016 Decision 7).
10. **Device loss.** From any remaining device, the user publishes a new signed device list revoking the lost device. The server ends its sessions and refuses its connections at once, and the user's devices remove it from every group with MLS commits. If the lost device was native, it held the device-signing key, so the user rotates that key with the recovery kit or passkey unlock. The remaining devices' places in groups stay valid under item 2's rule. Without a remaining device, the user recovers (items 5–8).
11. **Exposure.** If the recovery kit or a passkey with passkey unlock may have been exposed, or a device alarms (item 3):
    - The user makes a new recovery kit, a new key-backup key (devices seal the current snapshot keys to it again) and a new device-signing key, and certifies the remaining devices again.
    - If a hostile party may hold an older secret store, the user also makes a new identity key, which contacts see as a change.
    - Every recovery ends with a new kit and a new key-backup key, because a recovery may run on a device or in a browser the user does not fully trust.
12. **Cryptography.** Everything here uses Ed25519, HKDF, AEAD and HPKE, including the hybrid KEM, as provided by OpenMLS's crypto provider; no other primitive, no password hashing, no password-authenticated key exchange and no secret sharing is used (ADR-0016 Decision 12). The constructions that combine them are device certificates and device lists, the secret store, the key backup, passkey wrapping, the authenticated approval exchange, link signing (threat model F5) and the device's proof of possession; the external audit before collaboration leaves beta reviews them (SEC-08). The Phase-3 work package specifies every byte format, label and associated data, with test vectors.

## Consequences

- A user who keeps the recovery kit gets back their identity and every document after losing all devices, and a document whose only owner lost every device can be managed again.
- A sign-in taken over through an identity provider, a passkey or an administrator does not give keys or a trusted device.
- Web code that a hostile server serves once can take a browser device's keys (T11) but cannot certify devices or sign device lists, so revoking that browser device ends the damage; until then, what is shared with that account is exposed through it.
- Users without a native device must use the recovery kit to approve new devices.
- The recovery kit becomes the root of the account: whoever holds it owns the account, and with the server's stored data reads the latest snapshot of every document until the user responds as in item 11 (threat T28). Recovery joins are visible to every member, which makes their abuse noticeable but not impossible (T39).
- The server stores three new kinds of ciphertext (secret store, key backup, passkey wraps), pending approvals and the directory; the threat model's metadata inventory (§9) lists them.
- The validator and every client must check credential chains, device lists, resyncs and recovery joins; the Phase-1 server work packages prepare for it (device-bound sessions, pending devices) and Phase 3 builds it.
- At first contact without verification, users still trust the server's directory, until key transparency.
- Without an expert review before Phase 3, the constructions of item 12 rest on the Phase-3 work package's specification, test vectors and code review until the external audit before collaboration leaves beta; a flaw that the audit finds then means changing code that is already built.

## Alternatives considered

- **The device-signing key on every device, browsers included:** simpler approvals, but web code served once could copy it and keep certifying the server's devices, and could even sign device lists that undo the user's revocations, until the user rotated the key.
- **The identity key on every approved device:** one key fewer, but a stolen device could certify devices until the user replaced the identity key itself, which every contact would see as a new identity and have to re-verify.
- **The identity key needed for every approval:** the recovery kit at every new device; contradicts COL-13's approval from a trusted device and trains users to type their kit often.
- **HPKE alone for the approval:** HPKE's base mode does not authenticate the sender, so the server could hand the new device keys of its own.
- **Owners re-add a recovered user instead of recovery joins:** leaves documents whose only owner lost every device frozen for good, and documents only the user held unreadable.
- **A passphrase instead of a generated kit:** needs a password-hashing function outside MLS's providers (an ADR and an expert review under ADR-0016 Decision 12) and lets the server try guesses against the stored ciphertext.
- **Recovery held partly by the server, or by friends (secret sharing):** the first breaks the zero-knowledge invariant (ADR-0015 Decision 6); the second needs secret sharing, which MLS's providers do not include, and a design of its own.
- **Approving with a short code typed on the other device:** without a password-authenticated key exchange, the server can guess such a code offline and approve its own device.
- **Key transparency now:** the IETF protocol is still a draft and no implementation has been chosen; re-evaluated at the Phase-3 gate.

## Validation gate

The Phase-3 work package that builds identity and recovery (epic E3-DEVICES-KEYS in [plan/05](../plan/05-work-breakdown.md)) must show, natively and in WebAssembly, with tests:

- chains checked by the validator and by clients, including refusal of a broken or revoked chain, and existing leaves that stay valid after a rotation of the device-signing key;
- approval refusing a pending device whose keys differ from the scanned or compared ones;
- a new device refusing an approval not authenticated with the out-of-band secret;
- browser devices never receiving the device-signing key;
- recovery on a new device that rejoins a document whose only owner was the recovered user and then removes the lost devices, and a private document read from the key backup;
- a resync by a device that fell behind;
- refusal of a recovery join or resync that changes the roster, removes another user's device, or comes from a revoked device;
- an alarm when the device list changes in a device's name without that device;
- device loss followed by rotation of the device-signing key.

The external audit (SEC-08) follows. The proposal also asked for an expert review of the constructions of item 12 before that work package starts; the owner decided against it on 2026-10-17, so the external audit is their first review from outside the project.

## Revisit when

The IETF publishes key transparency or an audited implementation fits the stack; OpenMLS lets an external commit remove a leaf that the application accepts; post-quantum signatures are adopted (ADR-0016, amendment 2026-10-04); MLS's extensions (draft-ietf-mls-extensions) are published; platforms let apps use passkeys for any domain; the external audit asks for changes.
