# ADR-0008: CRDT engine (Loro) and local-first architecture

- **Status:** Accepted — validation gate (CORE-004 reported 2026-10-07, revised 2026-10-08: criteria partly met; the owner's decision on the recommended conditions is pending)
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** COL-01…COL-08, ADR-0007, ADR-0016, CORE-004

## Context

Co-authoring must work without locks, offline, and through a server that cannot read the data (so the server cannot transform or merge operations, ruling out server-centric operational transformation). Conflict-free replicated data types (CRDTs) meet these needs. Writing our own rich-text CRDT would be a multi-year research effort. Candidates verified on 2026-10-03:

| Library | Facts |
|---|---|
| **Loro** (`loro` 1.16.2, MIT) | Rust core with WebAssembly bindings (about 1.1 MB gzipped); encoding stable since 1.0 (Oct 2024); Peritext-style rich text with per-key mark expansion (`before`/`after`/`both`/`none`); maps, movable lists, movable trees; undo manager; shallow snapshots for history trimming; ephemeral presence store; checkout of past versions. Small team; recent releases still fix crashes on malformed imports. |
| **Automerge 3** (Rust 0.12, MIT) | Mature; 3.0 (July 2025) cut memory use more than tenfold; rich text with marks and block markers; built-in sync protocol; **no undo in the core library**. |
| **Yjs / yrs** (MIT) | Very widely used, but formatting is stored as inline markers with known concurrent-formatting anomalies, and yrs removed list move support in 0.27. |

## Decision

1. **Use Loro** as the CRDT engine, accessed only through the `bayan-crdt` adapter crate, which exposes BayanDocs-shaped primitives (story sequences with marks, property maps, movable row and cell lists, an undo manager, snapshots, version checkout). No other crate imports Loro directly.
2. **Mapping:** stories map to rich-text sequences in which special atoms are placeholder code points that cannot occur in imported text, with their payload referenced through marks or keyed maps; paragraph and object properties map to maps; table rows and cells map to movable lists. Do **not** adopt nested-tree editor bindings (such as ProseMirror-style trees); the flat story model is the point (ADR-0007).
3. **Local-first by default.** Every document, even a single user's local file, is edited through the CRDT. The `.docx` file is the interchange and save format; CRDT state is kept in the auto-recovery journal, the local version history, and (when collaborating) the encrypted sync log.
4. **Untrusted updates:** CRDT updates from other clients are untrusted input. They are authenticated (signed through MLS, ADR-0016) before import, imported with resource limits, and the import path is fuzzed. On the web, import runs inside the engine worker.
5. **Undo** uses the CRDT's local undo manager so that undo affects only the user's own changes, as users expect in collaborative editors.
6. **History** is trimmed with shallow snapshots according to a retention policy; named versions are kept.
7. **Fallback:** if CORE-004 fails its criteria, Automerge 3 behind the same adapter is the alternative (requiring our own undo implementation).

## Consequences

- Offline editing and merge come from the architecture rather than special cases.
- The core inherits Loro's encoding format; the adapter and the 1.x stability promise contain that risk.
- WebAssembly size grows by roughly 1 MB gzipped; acceptable within PERF-06.

## Alternatives considered

- Automerge 3 (fallback), Yjs/yrs, our own CRDT, server-ordered operational transformation (incompatible with zero-knowledge servers and long offline periods). See context.

## Validation gate

CORE-004 must show, on the BDM mapping: convergence and valid normalization in 100% of 1,000 randomized three-replica runs of 10,000 operations; correct mark-expansion behavior for Word-style formatting, hyperlinks and comments (including many concurrent comment ranges); undo that reverts only local changes; and, for a synthetic 500-page document in WebAssembly, load time, memory and update sizes within the limits recorded in the work package. A comparison run on Automerge 3 is included for reference.

## Validation result (CORE-004, 2026-10-07; revised 2026-10-08 after review)

The [CORE-004 report](https://github.com/BayanDocs/bayan-core/pull/13) (`spikes/crdt-model/REPORT.md` in bayan-core) has the evidence; measurements are on a 500-page synthetic document (1.5 million characters, 15,000 paragraphs, 200 tables, 2,000 comments).

- **Met:** convergence and valid normalization in 100% of 1,000 three-replica runs of 10,000 operations (the first run; the re-run on the code after the review is in progress); mark expansion for run properties, hyperlinks and comments, including many overlapping comments (Loro configures expansion by the part of a key before its first colon, so `cmt:<id>` keys need one configured family); undo that reverts only local changes; WebAssembly memory (142 MB after loading and reading; limit 300 MB); update sizes (about 105 bytes per edit).
- **Not met:** load time. Loro 1.16.2 decodes rich text from snapshots in quadratic time, so loading and reading the document takes 2.6 s natively and 7.0 s in WebAssembly (limits 0.3 s and 1 s). With a three-line fix to Loro, measured on a patched copy, it takes 0.51 s and 0.76 s. Applying a 1,000-operation update takes 58 ms natively and 95 ms in WebAssembly (limit 50 ms) the first time after opening, and 8 ms and 13 ms afterwards.
- **History trimming (decision 6):** in Loro 1.16.2 a document opened from a shallow snapshot is slower than one opened from a full snapshot (with the decoding fix: the first update after opening 271 ms instead of 61 ms, an undo step 408 ms instead of 203 ms, and every keystroke that crosses one of the receiver's own 207 ms instead of 0.14 ms), so the storage and sync work packages must measure the trade-off before choosing the at-rest format.
- **Untrusted updates:** fuzzing found that Loro panics on crafted updates whose checksum is valid, aborts the process on crafted change headers that request absurd allocations, and overflows the stack on deeply nested values, all while decoding, which Loro also does to count the changes and operations that the adapter's limits check. The adapter imports with limits, contains panics (the replica is poisoned, refuses everything afterwards and is discarded) and refuses values nested too deeply among those that survive decoding; allocation failures and stack overflows cannot be contained inside the process, so imports from untrusted peers need isolation.
- **Platform calls:** Loro draws a random peer identifier for every new document (in the browser build through `crypto.getRandomValues`) and its undo manager reads the wall clock, which ADR-0012 does not allow the core to do. Neither changes content; how to treat them is the owner's decision (report §8.4).
- **Dependencies:** `deny.toml` accepts six RustSec advisories for crates that Loro depends on, pending the owner's review: four unmaintained crates, and two memory-safety defects (in im's `OrdSet` and in sized-chunks' `Chunk`) in code that Loro does not reach (report §10).
- **Automerge 3** (the fallback of decision 7), on the same text, marks and block markers: loading and reading 1.5 s natively and 2.6 s in WebAssembly, 330 to 400 MB of memory, 0.8 s natively and 1.2 s in WebAssembly to apply a 1,000-change update, and about 0.4 s natively for every update however small. Its snapshots are five times smaller (0.93 MB against Loro's 5.0 MB) and its update for a whole session 14% smaller (15,024 against 17,559 bytes). It is not a better choice.
- **Recommendation of the report (for the owner's decision; not binding until accepted as an amendment):** confirm Loro on three conditions: the quadratic decoding is fixed upstream before the model work packages measure loading again; the engine's hosts isolate the import of untrusted updates and restart an engine that aborts; CORE-101 addresses the cost of per-paragraph maps, the latency of applying updates and the latency of undo (about 0.2 s per step in a 500-page document). The report also drafts upstream issues for every Loro finding; the crash reports should go to Loro's maintainers privately and soon, because the committed fuzzer regenerates the reproductions.

## Revisit when

The validation gate fails; Loro's maintenance falters (no release for 12 months, or the encoding stability promise is broken); or Automerge gains capabilities that change the comparison.
