# ADR-0030: Commit acceptance, departures and group repair

- **Status:** Proposed (SRV-003, 2026-10-14). Not binding until the owner accepts it; the external audit before collaboration leaves beta covers it (SEC-08).
- **Date:** 2026-10-14
- **Deciders:** proposed by the SRV-003 implementer session; the owner decides (ADR-0001 Decision 5: it changes a security design)
- **Related:** COL-01, COL-05, SEC-08, SEC-13, OPS-04, [ADR-0015](0015-server-architecture.md), [ADR-0016](0016-e2ee-and-identity.md), [ADR-0029](0029-identity-devices-and-recovery.md), [threat model v1](../specs/threat-model.md) (§7, flows F4, F12, F13, F17; threats T25, T26, T33), SRV-002, SRV-003, SRV-103, SRV-104, SRV-105

## Context

The server's validator cannot check the parts of an MLS commit that are keyed with the epoch's secrets: its membership and confirmation tags and the path secrets it encrypts to the other members. Any member, a viewer included, can therefore send a commit that the server accepts and every other member refuses; the server then follows the group into an epoch the members never reach and refuses all their later commits (SRV-002 report §5). On 2026-10-09 the owner chose two-phase acceptance at the server as the direction against this, with an owner's move to a new group that may leave users out as the manual last resort, and asked SRV-003 to design the details (ADR-0016, amendment 2026-10-07, requirement 6). The threat model v1 (§7) does so and finds three more gaps in the same area:

1. **A user cannot leave a document without an owner.** A regular commit cannot remove its own committer (RFC 9420 §12.2), and the design refuses standalone proposals, so a user's last device in a group can be removed only by an owner.
2. **A server restored from a backup stalls groups.** Every group that changed after the backup is ahead of the restored server, which refuses its members' commits as being for the wrong epoch; sessions revoked after the backup come back; key packages that were already used are offered again.
3. **Server and clients must apply the same rules.** If the validator and a client run different versions of the role policy, one accepts what the other refuses.

Facts verified on 2026-10-14 in the source of OpenMLS 0.9.0, the pinned version: a member's own commit stays pending until the member merges or clears it (`MlsGroupState::PendingCommit`); a member can process another member's commit into a staged commit and decide later whether to merge it; and `MlsGroup::create_message` refuses only when the member has left the group or holds stored proposals, so a member can keep sending application messages while its own commit is pending, as long as its commit carries its proposals inline. The `SelfRemove` proposal, with which a member asks to leave, comes from the MLS extensions draft (draft-ietf-mls-extensions, draft-09 of March 2026, not yet an RFC); OpenMLS 0.9.0 implements it.

## Decision

1. **Which commits take two phases.** A commit takes two phases when its committer's account is not an owner in the epoch before it: self-updates, changes to the committer's own devices, and recovery joins (ADR-0029) by users who are not owners. Owners' commits and group registrations take effect at once, as the SRV-002 validator does today: owners can already remove anyone, and making them wait would delay every share to someone who is offline.
2. **Pending.** The validator checks a commit as it does today. If the commit passes and no other commit is pending in the group, it becomes the group's pending commit: the server stores the public state after it next to the current one, in the database, relays the commit marked as pending, and holds any Welcome it carries. While it is pending, the server accepts updates for the current and the previous epoch but none for the pending epoch; refuses other commits by users who are not owners, with a reason that asks them to retry; and accepts an owner's commit for the current epoch, which drops the pending commit as superseded.
3. **Witnesses report.** A witness is a device of another account that is a member both before and after the commit. Each witness device that receives a pending commit processes it without merging it and reports, over its authenticated connection, either OK or a refusal with one reason class (`tag`, `path`, `policy`, `credential`, `malformed`). Devices witness the pending commits of all their groups in the background when they connect. The server keeps each device's first report and counts accounts, not devices.
4. **The server decides.** An owner's report decides at once: OK confirms, a refusal drops. Otherwise the first report starts a grace period (proposed: 10 seconds); at its end, only OK reports confirm, only refusals drop, and both, from different accounts, make the commit disputed. A disputed commit waits for an owner's report, which decides, and is dropped if none comes within a limit (proposed: 72 hours). A commit that no witness reports on within a longer limit (proposed: 7 days) is confirmed, because nobody else is active in the group and refusing would block users' own device changes in quiet groups for good. SRV-103 measures the three limits and may change them.
5. **Outcomes.** On confirmation the new epoch becomes current, held Welcomes are delivered, and every device merges the commit. On a drop every device discards it, and unless the commit was superseded or disputed, the committing device is quarantined: the server refuses its commits, not its updates, until an owner lifts the quarantine or removes the device. Owners are told of every drop, dispute and quarantine, without content. Nobody, the committer included, merges a commit before the server confirms it.
6. **Devices left behind.** A device that refused a commit that was then confirmed reports that it is stuck; an owner's client re-adds it with a fresh key package, or the device rejoins with a recovery join (ADR-0029). An owner's move to a new group that may leave users out (ADR-0016, amendment 2026-10-07, design detail 4 and requirement 6) remains the manual last resort, for example when a compromised owner device stalls a group.
7. **Leaving a document.** A device that leaves sends a leave request as an MLS application message, which authenticates it to the members, and tells the server, which stops delivering to it at once. An owner's client then commits the removal. When the MLS extensions draft is published with a final code point for `SelfRemove`, the design adopts that proposal instead, as the one standalone proposal the validator accepts, which any member's next commit must include.
8. **One policy version.** The roster extension carries the version of the role policy. The validator and clients refuse a group, a commit or a Welcome with a version they do not know, and a change of the policy is a migration that owners carry out.
9. **After a restore.** After restoring a backup, the server ends every session, marks every stored key package and pending state as stale, and asks devices for new key packages. Members then send again the commits the server lacks, oldest first, each checked as usual, and the newest signed device lists they hold; the sync protocol (SRV-104) carries this.
10. **The kind of an update stays encrypted.** As ADR-0016's amendment of 2026-10-07 (design detail 3) asked SRV-003 to confirm: the server is not told whether an update is an edit or a comment (threat model §7.4).

## Consequences

- A single member can no longer stall a group by itself; a stalled group repairs itself automatically in the common case and with an owner's decision in a dispute.
- Commits by users who are not owners take effect one round trip to another user's online device, plus the grace period, later; owners' commits are not delayed. Clients must hold staged commits, report on them, witness in the background and recognize when they are stuck; this is work for `bayan-mls` and `bayan-sync` in Phase 3.
- The server keeps one more copy of the public state per group with a pending commit (at most 1.34 MiB at 1,000 members with the hybrid suite, SRV-002) and the reports until a decision.
- A liar can delay commits of users who are not owners and get honest devices quarantined until an owner acts; colluding users can force owners to decide disputes; a group in which nobody else connects for 7 days can still be stalled. The threat model lists these as residual (§12).
- Users can leave without waiting for an owner's goodwill, but their leaf stays in the tree until an owner commits the removal.
- A restore no longer stalls groups for good, but they wait until their members reconnect.

## Alternatives considered

- **Two phases for every commit, owners' too:** protects against a compromised owner device, but every share to people who are offline would block the next membership change in that group; an owner's move already repairs that case.
- **Confirm on the first OK, without a grace period:** faster, but a colluding member's quick OK would win against an honest refusal arriving a moment later.
- **Drop when no witness reports in time:** stalls nothing, but blocks users' own device changes in groups where nobody else is active.
- **Resync by external commits only, as the main defense (SRV-002 report option 2):** every stuck member must rejoin in turn and the culprit stays until an owner acts; kept for recovery (ADR-0029) and for devices left behind.
- **Majority voting among witnesses:** needs many online witnesses, which most groups do not have, and is no stronger against colluding users than owners deciding.
- **The update's kind in MLS's authenticated data,** so that the server could refuse commenters' edits: rejected again for the reasons in the threat model's §7.4.

## Validation gate

SRV-103 and the Phase-3 work package that builds `bayan-mls` must show, with tests that include a hostile test client: a corrupted commit by a viewer dropped and its device quarantined while the group continues; a lying witness unable to drop a commit that an owner or another witness confirms; a dispute decided by an owner; a stuck device repaired by an owner's re-add and by a recovery join; an owner's commit superseding a pending one; a leave request followed by an owner's removal; refusal of an unknown policy version; and a server restored from a backup that catches up from its members' re-sent commits.

## Revisit when

The MLS extensions draft is published (SelfRemove); OpenMLS implements re-initialization (`ReInit`); the measurements of SRV-103 suggest other limits; the external audit asks for changes; MLS gains a way for a delivery service to check commits without the epoch's secrets.
