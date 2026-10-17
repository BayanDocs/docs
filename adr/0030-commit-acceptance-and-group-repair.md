# ADR-0030: Commit acceptance, departures and group repair

- **Status:** Accepted (owner, 2026-10-17), including the three departures from the owner's earlier direction listed under Context — validation gate (SRV-103 and the Phase-3 work package that builds `bayan-mls` and `bayan-sync`, below); the external audit before collaboration leaves beta covers it (SEC-08).
- **Date:** 2026-10-14 (proposed); 2026-10-17 (accepted)
- **Deciders:** Owner, on 2026-10-17, answering the open questions of SRV-003's [pull request](https://github.com/BayanDocs/docs/pull/42), on the recommendation of the SRV-003 implementer session (ADR-0001 Decision 5: it changes a security design)
- **Related:** COL-01, COL-05, SEC-08, SEC-13, OPS-04, [ADR-0015](0015-server-architecture.md), [ADR-0016](0016-e2ee-and-identity.md), [ADR-0029](0029-identity-devices-and-recovery.md), [threat model v1](../specs/threat-model.md) (§7, flows F4, F9, F12, F13, F17; threats T25, T26, T33; failure modes FM1–FM13), SRV-002, SRV-003, SRV-103, SRV-104, SRV-105

## Context

The server's validator cannot check the parts of an MLS commit that are keyed with the epoch's secrets: its membership and confirmation tags and the path secrets it encrypts to the other members. Any member, a viewer included, can therefore send a commit that the server accepts and other members refuse; the server then follows the group into an epoch those members never reach and refuses all their later commits (SRV-002 report §5). The committer can also encrypt correctly to some members and wrongly to others ("selective encryption"), so a commit can work for the owners' devices and fail for everyone else, or work for the members who are online and fail for those who are offline.

On 2026-10-09 the owner chose a direction against this: the server keeps the previous epoch's public state until a device of another user confirms the new epoch, and otherwise drops the commit and quarantines its sender; an owner's move to a new group that may leave users out stays the manual last resort. The owner asked SRV-003 to design the details (ADR-0016, amendment 2026-10-07, requirement 6). The threat model v1 (§7.2) does so, and departs from the chosen direction in three points, which the owner accepted explicitly on 2026-10-17:

1. **Owners' commits take effect at once.** The direction covers every commit; this ADR applies two phases only to commits by members who are not owners (Decision 1 says why).
2. **A commit that nobody checks within 72 hours is dropped without quarantine.** The direction drops and quarantines "otherwise"; a time-out is not evidence of misbehavior, so its sender is not punished and may retry.
3. **Quarantine covers the sender's account in that group, not one device,** so that a quarantined member cannot start again with another of its devices or a new one.

The threat model also finds three more gaps in the same area:

1. **A user cannot leave a document without an owner.** A regular commit cannot remove its own committer (RFC 9420 §12.2), and the design refuses standalone proposals, so a user's last device in a group can be removed only by an owner.
2. **A server restored from a backup stalls groups.** Every group that changed after the backup is ahead of the restored server, which refuses its members' commits as being for the wrong epoch; sessions ended after the backup come back; key packages that were already used are offered again.
3. **Server and clients must apply the same rules.** If the validator and a client run different versions of the role policy, one accepts what the other refuses.

Facts verified on 2026-10-14 in the source of OpenMLS 0.9.0, the pinned version:

- A member's own commit stays pending until the member merges or clears it (`MlsGroupState::PendingCommit`), and a member can process another member's commit into a staged commit and decide later whether to merge it.
- `MlsGroup::create_message` refuses only when the member has left the group or holds stored proposals. A member can therefore keep sending application messages while its own commit is pending, as long as the commit carries its proposals inline, which this design's commits always do. Conversely, a member that has stored a proposal received from someone else, as it must to process a later commit that includes that proposal by reference, cannot send application messages until it merges a commit that empties its proposal store.
- OpenMLS implements the `SelfRemove` proposal, with which a member asks to leave (`leave_group_via_self_remove`), always in public framing; its external commits can include other members' `SelfRemove` proposals. The proposal comes from the MLS extensions draft (draft-ietf-mls-extensions, draft-09 of March 2026), which is not yet an RFC, so its code point is not final.
- OpenMLS's public group, which the server's validator uses, cannot be copied (see the SRV-002 spike's `validator.rs`), so the server cannot keep a staged state in memory alone across restarts.

## Decision

1. **Which commits take two phases.** A commit takes two phases when its committer's account is not an owner in the epoch before it: self-updates, changes to the committer's own devices, and resyncs and recovery joins (ADR-0029) by users who are not owners. Owners' commits and group registrations take effect at once, as the SRV-002 validator does today. Two phases would add little against a malicious owner, who can already remove anyone, and another owner's move repairs a group that an owner's bad commit stalls. They would cost a lot: under Decision 4 a single lying member could drop every owner's commit except its own removal, which it cannot witness, so shares and role changes would stop until an owner removed it; every share would wait until another member's device comes online; and the first share of a document that only its owner belongs to could never be confirmed, because nobody could witness it.
2. **Pending.** The validator checks the commit exactly as the SRV-002 validator does. If it passes and no other commit is pending in the group, it becomes the group's pending commit: the server stores the commit in the database next to the current state and stages it again after a restart, relays it marked as pending, and holds any Welcome it carries until it is confirmed. While a commit is pending, the server:
   - accepts updates for the current and the previous epoch, as today, but none for the pending epoch;
   - refuses other commits by users who are not owners, with a reason that asks them to retry;
   - accepts an owner's commit for the current epoch, which drops the pending commit as *superseded*, without quarantine.
3. **Witnesses and their reports.**
   - A witness is a device of an account other than the committer's that is a member both before and after the commit. For resyncs and recovery joins, the joining account's own other devices, which know every revocation, may also refuse, but their OK does not count.
   - Every witness device that receives the pending commit processes it without merging it, checks the group information that the committer published with it, and reports, over its authenticated connection, either OK or a refusal with one reason class: `tag` (a membership or confirmation tag is wrong), `path` (its path secret does not decrypt or does not fit), `group-info` (the published group information does not match the epoch it derived), `policy` (its own policy check refuses what the validator accepted), `credential` (a chain or a revocation is wrong) or `malformed`.
   - The server keeps the first report of each device and counts accounts, not devices. Devices witness the pending commits of all their groups in the background when they connect, not only those of documents that are open.
4. **The decision.**
   - The first report starts a grace period, 10 seconds by default. At its end, the commit is *confirmed* if at least one witness account reported OK and none refused.
   - A single refusal *drops* it. A commit made honestly can be processed by every member, so a refusal means either a bad commit or a lying witness, and a lying witness is the smaller harm (Consequences).
   - An owner's report counts like anyone else's, because a committer can make a commit work for the owners' devices alone.
   - If no witness reports within 72 hours, the commit *expires*: it is dropped without quarantine, and its committer may retry.
5. **Outcomes.**
   - *Confirmed:* the new epoch becomes current and the old one is kept as the previous epoch; held Welcomes are delivered; every device merges the commit, the committer its pending commit.
   - *Dropped, expired or superseded:* the server discards the new state, and every device discards the commit, the committer by clearing its pending commit.
   - *After a drop,* the committer's **account** is *quarantined* in the group: the server refuses commits by any of its devices, resyncs and recovery joins included, but not its updates, until an owner lifts the quarantine or removes the account.
   - Owners are told about every drop, quarantine and stuck report, with the reason classes and without content. Nobody, the committer included, merges a commit before the server confirms it.
6. **Devices left behind.**
   - A witness device that cannot process a commit that was confirmed while it was offline reports that it is stuck, with a reason class.
   - A stuck report with reason `tag`, `path` or `group-info` quarantines the committer's account afterwards, because the commit was bad for some members, and owners are told.
   - The stuck device resyncs with its own device key, using group information that a member who processed the epoch published (ADR-0029), or an owner's client re-adds it with a fresh key package.
   - An owner's move to a new group that may leave users out (ADR-0016, amendment 2026-10-07, design detail 4 and requirement 6) remains the manual last resort, for example when a compromised or broken owner device stalls a group with a one-phase commit.
7. **Leaving a document.**
   - A user leaves a document with a leave request, sent from one of their devices as an MLS application message, which authenticates it to the members. The device also tells the server, which at once stops delivering the group's messages to all of the user's devices. An owner's client then commits the removal of the user's devices and role. The last owner must first make another member an owner, because every commit leaves at least one.
   - When the MLS extensions draft is published with a final code point for `SelfRemove`, the design evaluates adopting it in place of the leave request (Revisit when). Adopting it needs two changes: the validator accepts `SelfRemove` as the one standalone proposal, and the role policy lets a commit by any member include another member's `SelfRemove`, while every other removal of another user's device stays reserved to owners. It also has a cost in OpenMLS 0.9.0: from the moment members store a `SelfRemove` until they merge the commit that covers it, which takes at least the grace period of Decision 4 for a commit by a member who is not an owner, they cannot send edits.
8. **One policy version.** The roster extension carries the version of the role policy. The validator and clients refuse a group, a commit or a Welcome with a version they do not know. A change of the policy is a migration that owners carry out, with an owner's commit that changes the version, once servers and clients know the new version.
9. **Catching up after a restore** (threat model §7.5):
   - After restoring a backup, the server ends every session, marks every stored key package and pending commit as stale, and puts every group in *catch-up*.
   - Member devices upload the commits they merged after the server's restored epoch, oldest first. Each is checked against the public state and the policy as usual, with two differences: its signature, not the uploading connection, shows who made it; and it is not witnessed again, because its members already merged it.
   - A commit is accepted only if a device of another account uploads it, or an owner's device does, or the group has only one account, so that a member cannot slip in its own commit that was dropped before the restore.
   - If devices upload different commits for the same epoch, the server stops catching up that group and tells its owners; the chain an owner's device uploads decides, and members on the other branch resync.
   - Devices also upload the newest signed device lists they hold, which the server accepts when they are newer and correctly signed, and replace their key packages. Lost updates and snapshots are sent again from members' CRDT state through the normal sync protocol (SRV-104).
10. **The kind of an update stays encrypted.** As ADR-0016's amendment of 2026-10-07 (design detail 3) asked SRV-003 to confirm: the server is not told whether an update is an edit or a comment (threat model §7.4).

## Consequences

- A single member can no longer stall a group by itself: its bad commit is dropped at the first refusal and its account quarantined, and a commit that turns out bad for members who were offline gets its committer quarantined afterwards while those members resync.
- A lying witness can drop honest commits by members who are not owners, or report them as stuck after they were confirmed, and so get their accounts quarantined until an owner acts (FM12). Owners see who refused or reported what and can remove the liar. This ADR accepts that harm to avoid the larger one, a group stalled by a bad commit.
- Commits by users who are not owners take effect one round trip to another user's online device plus the grace period later; owners' commits are not delayed. In a group that no other member visits, members who are not owners cannot change their keys or devices until someone does; their commits expire after 72 hours and they retry.
- An owner's commit that members cannot process still stalls the group. That needs a compromised or broken owner device, and another owner's move (threat model F13) repairs it; in a group with a single owner, that owner's move from another device, or after a recovery, does.
- Clients must hold staged commits, report on them, witness in the background, recognize when they are stuck and resync; this is work for `bayan-mls` and `bayan-sync` in Phase 3.
- The server keeps one more copy of the public state per group with a pending commit (at most 1.34 MiB at 1,000 members with the hybrid suite, SRV-002), the reports for 30 days after the decision, and the quarantines (threat model §9.1).
- Users can leave without waiting for an owner's goodwill: the server stops delivering to them at once. Their leaf stays in the tree, and their device keeps the keys of the epochs it held, until an owner commits the removal.
- A restore no longer stalls groups for good, but they wait until their members reconnect. Reports and quarantines recorded after the backup are lost: a quarantined account can commit again, and if it sends another bad commit, witnesses drop it and its account is quarantined again.

## Alternatives considered

- **Two phases for every commit, owners' too (the chosen direction as written):** protects against a compromised owner device, but a single lying member could then drop every owner's commit except its own removal, stopping shares and role changes until an owner removed it; every share would wait for another member to come online; and nobody could witness the first share of a document that only its owner belongs to. An owner's move already repairs the compromised-owner case.
- **An owner's report decides at once, and a dispute between OK and refusal waits for an owner:** a committer can make a commit work for the owners' devices alone, so an owner's OK proves nothing about the other members, and a disputed commit would hold the group's single pending slot for days.
- **Confirming after a time-out without reports (optimistic confirmation):** a time-out is not evidence that the commit is good; a bad commit would be confirmed unwitnessed and stall the group when its members come back.
- **Dropping and quarantining after a time-out (the chosen direction as written):** a time-out is not evidence of misbehavior; quarantine would punish members of quiet groups.
- **Quarantining the committing device only:** the same account could try again from another of its devices or a new one.
- **Confirming on the first OK, without a grace period:** a colluding member's quick OK would win against an honest refusal arriving a moment later.
- **Majority voting among witnesses:** needs many online witnesses, which most groups do not have, and a committer can make a commit work for a majority.
- **Resync by external commits only, as the main defense (SRV-002 report option 2):** every stuck member must rejoin in turn and the culprit stays until an owner acts; kept for recovery (ADR-0029) and for devices left behind.
- **Standalone Remove proposals by the leaving member, now (RFC 9420 §12.1.3):** works without the extensions draft, but has the same cost as `SelfRemove` in OpenMLS 0.9.0 (members cannot send edits while they hold the proposal) and needs the same policy exception, without `SelfRemove`'s advantage that external commits can include it.
- **The update's kind in MLS's authenticated data,** so that the server could refuse commenters' edits: rejected again for the reasons in the threat model's §7.4.

## Validation gate

SRV-103 builds the server side and the Phase-3 work package that builds `bayan-mls` and `bayan-sync` builds the client side; together they must show, with tests that include a hostile test client:

- a corrupted commit by a viewer dropped at the first refusal and its account quarantined while the group continues;
- a selectively encrypted commit that works for the owners' devices only, dropped by another member's refusal although an owner reported OK;
- a commit confirmed while some members were offline, followed by those members' stuck reports, the committer's account quarantined afterwards, and the members' resyncs;
- a lying witness's refusal dropping an honest commit, and its false stuck report after a confirmation, each followed by an owner lifting the quarantine and removing the liar;
- a commit that expires after the time-out without quarantine, and its committer's retry;
- an owner's commit superseding a pending one;
- a stuck device repaired by a resync and by an owner's re-add;
- a pending commit that survives a server restart;
- a leave request that stops delivery to all the user's devices at once, followed by an owner's removal, and the last owner unable to leave before making another member an owner;
- refusal of an unknown policy version;
- a server restored from a backup that catches up from its members' uploaded commits, including refusal of a dropped commit re-uploaded by its own committer, and a fork decided by an owner's chain.

## Revisit when

The MLS extensions draft is published (`SelfRemove`, Decision 7); OpenMLS lets members send application messages while they hold proposals, or implements re-initialization (`ReInit`); the measurements of SRV-103 suggest other limits; the external audit asks for changes; MLS gains a way for a delivery service to check commits without the epoch's secrets.
