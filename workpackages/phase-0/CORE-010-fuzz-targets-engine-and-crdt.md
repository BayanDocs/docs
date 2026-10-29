# CORE-010: Fuzz targets for the engine boundary and CRDT updates, and private crash reports

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | SECURITY / MODEL |
| Repository | bayan-core (`fuzz/`, `.github/workflows/fuzz.yml`) |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | CORE-004, CORE-005, CORE-006, CORE-007 |
| Unblocks | ADR-0008 decision 4 ("the import path is fuzzed"); CORE-101 and CORE-125, which extend these targets |
| Status | Ready |
| Requirements | SEC-07, SEC-13, REL-05, ARC-07 |
| Decisions | ADR-0006, ADR-0008, ADR-0012, ADR-0017, ADR-0025 |
| Specs | [engine-protocol.md §10, §12, §13](../../specs/engine-protocol.md#10-record-and-replay), [threat-model.md §11](../../specs/threat-model.md#11-principal-threats) (T1, T3, T4, T7) |

## Context

*Fuzzing* feeds a parser millions of random and mutated inputs to find crashes, hangs and runaway memory. The architecture review of 2026-10-27, finding [H2](../../plan/reviews/2026-10-27.md#h2-fuzzing-never-runs-in-ci-and-four-kinds-of-untrusted-input-have-no-fuzz-target), found that fuzzing never ran in CI and that four kinds of untrusted input had no fuzz target at all.

**What is fixed.** bayan-core#21 (`c19898b`, 2026-10-27) added [`.github/workflows/fuzz.yml`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/.github/workflows/fuzz.yml) and `fuzz/ci.py`: every target is built with AddressSanitizer and runs for 150 seconds on each pull request that changes bayan-opc, bayan-xml, `fuzz/`, the root `Cargo.toml` or `.cargo/`, and for 15 minutes every night from a corpus that grows from night to night (the two default-limits targets twice as long); `ci.py` refuses to run when a target of `fuzz/Cargo.toml` has no settings. bayan-core#22 runs the supply-chain checks on `fuzz/Cargo.lock` first. There are ten targets today, all for bayan-opc and bayan-xml: `zip_archive`, `package`, `content_types`, `relationships`, `core_properties`, `compound_file`, `zip_archive_default_limits`, `package_default_limits`, `xml_reader` and `markup_compatibility` ([fuzz/README.md](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/fuzz/README.md)).

**What is left of H2** (checked on `3c5a18f`):

1. **Engine protocol messages, tile requests and the configuration have no target.** The engine's hostile-input test still calls itself "a deterministic, bounded stand-in for fuzzing until the fuzzing workspace exists" ([hostile_input.rs:3](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-engine/tests/engine/hostile_input.rs#L3)). The entry points are [`Engine::handle`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-engine/src/engine.rs#L386), [`Engine::render_tile`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-engine/src/engine.rs#L447) (the request behind `bayan_render_tile`) and [`Config::from_json`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-engine/src/config.rs#L61).
2. **Recordings that `diag.replay` reads have no target**, although the spec treats them as untrusted ([§10](../../specs/engine-protocol.md#10-record-and-replay)); the entry point is [`recording::replay`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-engine/src/recording.rs#L326).
3. **CRDT updates from other people have no target.** The only fuzzer is the CORE-004 spike's own mutator ([spikes/crdt-model/src/fuzz.rs](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/spikes/crdt-model/src/fuzz.rs#L3)), written before the owner accepted libFuzzer's license. The entry point is bayan-crdt's [`Doc::import`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-crdt/src/doc.rs#L277) with its presets `ImportLimits::UPDATE` and `ImportLimits::LOCAL_SNAPSHOT`. `import` contains Loro's panics and then poisons the document (`ImportError::Panicked`); the review's finding [M2](../../plan/reviews/2026-10-27.md#m2-the-crdt-adapter-does-not-guard-every-path-that-untrusted-bytes-take) adds three entry points without that guard, which CORE-101 will guard.
4. **The Fidelity Lab's own ZIP, package and XML readers have no target.** [CORE-011](CORE-011-retire-interim-parsers.md) removes them in favour of bayan-opc and bayan-xml, which are fuzzed, and adds a target for the scanner, so this work package leaves them alone.
5. **Crash inputs are published.** H2's recommendation 2 said that a crash is handled as a security report, never uploaded as a public artifact. bayan-core#21 chose otherwise: when a run fails, `fuzz.yml` uploads the failing inputs and every target's log as the artifact `fuzzing-failures` for 30 days ([fuzz.yml:137](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/.github/workflows/fuzz.yml#L137)), which anyone signed in to GitHub can download from a public repository. Its comment calls this acceptable "because every input comes from public files" ([fuzz.yml:4](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/.github/workflows/fuzz.yml#L4)), but a crashing input is new: found by mutation, it is a working proof of concept. libFuzzer also prints small crashing inputs into the log (as Base64). Every target reaches code of other projects (miniz_oxide, quick-xml, cfb, serde_json, and Loro with the new target), so a crash found at night can be an undisclosed vulnerability in their released software, which [SECURITY.md](../../SECURITY.md) asks everyone to keep private. The cfb case of finding [H3](../../plan/reviews/2026-10-27.md#h3-a-crafted-compound-file-makes-bayan-opc-use-about-a-thousand-times-its-size-in-memory) is withheld until the owner has reported it to cfb's maintainer; today's 64 KiB input limit for `compound_file` keeps its allocations below the 2 GiB that libFuzzer would report, but nothing in the workflow protects it.
6. **The documentation overstates.** The first line of `fuzz/README.md` still says that protocol messages have a fuzz target.

## Objective

Every kind of untrusted input that the review lists has a fuzz target that runs in CI on pull requests and every night, and no fuzzing run publishes a crashing input.

## Scope

### In scope

- **New targets** in `fuzz/`, each with settings in `TARGETS` of `fuzz/ci.py`, seeds, and a row in the README's table that says what it fuzzes and which properties it checks besides "no crash, no hang":
  - `engine_messages`: an engine created with a configuration whose test switches are off (so `diag.panic` is refused), a valid `hello` handshake done by the target, then the input split into messages for `Engine::handle`. Properties: no panic, also none that the engine catches; every answer is a valid protocol message (the engine's `schema` module, as `hostile_input.rs` checks); and a valid request after the hostile ones still succeeds.
  - `engine_tile`: `Engine::render_tile` with the request bytes and a size taken from the input, on an engine with the mock document open. Properties: no panic; a refused request leaves the engine usable.
  - `engine_config`: `Config::from_json`. Property: no panic; an accepted configuration starts an engine.
  - `engine_replay`: `recording::replay` with a fixed configuration. Properties: no panic; the recording is refused with a documented error or replayed.
  - `crdt_import`: `Doc::import` with both presets, seeded from snapshots and updates that real editing produces (including a second replica's concurrent edits), with the spike's structure-aware mutations ported into the target, for example through libfuzzer-sys's `fuzz_mutator!` (the spike stays as it is). Properties: no panic in BayanDocs code; a panic inside Loro may be contained by `import` (the owner accepted Loro with that guard, ADR-0008's amendment of 2026-10-08), after which the document is poisoned and behaves as `doc.rs` documents; anything else fails.
  - Two or more of these may share a binary if that is simpler, as long as each property is checked and `ci.py` names each target.
- **Panics the code under test catches.** libfuzzer-sys installs a panic hook that aborts on every panic, also on one that the code would catch; check this in the pinned version's source. That is right for the engine targets, whose handlers must never panic (bayan-ffi's silent hook is not linked into them). For `crdt_import`, install a hook that aborts unless the panic's location lies in Loro's code, so that panics contained by `import` are counted but not failures, and every panic in BayanDocs code is.
- **CI.** Extend the path filter of `fuzz.yml` to the crates the new targets build from their folders (at least `crates/bayan-engine/**` and `crates/bayan-crdt/**`). Check the jobs' time limits with five more targets (30 minutes on pull requests and 90 at night today) and adjust them, or split the targets, so that every target keeps its full time.
- **Private crash reports, for every target, old and new.** No crashing input, and no log that may contain one, is uploaded or printed where the public can read it. The job summary names each failing target and the kind of failure (crash, timeout, out of memory, leak) and nothing more. `fuzz/README.md` explains how to reproduce a failure in a private session (running the target locally from the seeds, as long as it takes) and that a crash is reported as SECURITY.md says: to the owner, and for another project's code by the owner to that project's maintainers. The comment at the top of `fuzz.yml` changes with it. If this has already been done as a separate task when this work package starts, keep it and apply it to the new targets.
- **Dependencies.** The fuzz workspace gains path dependencies on bayan-engine and bayan-crdt. Every package they bring into `fuzz/Cargo.lock` keeps the version and checksum of the main `Cargo.lock`; the gate's supply-chain checks and cargo-deny cover them. If cargo-deny needs the six advisory exceptions of Loro's dependencies (ADR-0008's amendment of 2026-10-08) in `fuzz/deny.toml`, copy them with the same reasons, so that the two policies still differ only by libFuzzer's NCSA license.
- **Documentation.** The first line and the targets table of `fuzz/README.md`, the comment of `hostile_input.rs` (it stays as a deterministic test beside the fuzzing), and bayan-core's `AGENTS.md` (the `fuzz/` row and the `fuzz.yml` row).

### Out of scope

- The lab's readers (CORE-011) and M2's unguarded entry points (CORE-101, which extends `crdt_import` to them).
- Fixing a crash in another project's code; that goes to its maintainers through the owner.
- Making the fuzzing job a required check: its path filter skips it on most pull requests.

## Deliverables

- New targets in `fuzz/fuzz_targets/` with their settings, seeds and, where useful, a dictionary (for example of the protocol's message types and field names).
- Changes to `fuzz/Cargo.toml`, `fuzz/Cargo.lock`, `fuzz/ci.py`, `fuzz/test_ci.py`, `fuzz/README.md`, `.github/workflows/fuzz.yml` and, if needed, `fuzz/deny.toml`.

## Acceptance criteria

- [ ] AC-1 The five targets (or fewer binaries that cover them) build with cargo-fuzz on the pinned nightly, and `fuzz.yml` runs them on the pull request (link to the run, with each target's executions and coverage in the job summary).
- [ ] AC-2 Each target checks the properties listed for it; for the engine targets, a test of the target's harness shows that a panic the engine catches still fails the run, and for `crdt_import`, that a panic in BayanDocs code fails it while a contained panic in Loro does not.
- [ ] AC-3 Each new target ran for at least 30 minutes in the session without a failure, or each failure in BayanDocs code is fixed with a regression test in the crate's own tests. A failure in another project's code is reported to the orchestrator privately (never in the pull request or a public issue), and the pull request says only that a report was made.
- [ ] AC-4 A failing run on a test branch (a target made to panic on purpose) shows that the job fails, names the target and the kind of failure, and publishes neither the input nor the log (link to that run, then revert).
- [ ] AC-5 `cargo xtask verify` passes, including the supply-chain checks and cargo-deny for the fuzz workspace; the pull request lists every package that `fuzz/Cargo.lock` gains, each at the version of the main `Cargo.lock`.
- [ ] AC-6 `fuzz/test_ci.py` covers the new settings and the private failure report.
- [ ] AC-7 The README's first line, its table, `hostile_input.rs`'s comment and bayan-core's `AGENTS.md` are correct.

## Verification

`cargo xtask verify`; `cargo +nightly-2026-10-02 fuzz build --target x86_64-unknown-linux-gnu`; `python3 -I fuzz/ci.py seeds fuzz/seeds` and `python3 -I fuzz/ci.py run <targets> --seconds 1800 --seeds fuzz/seeds`; `python3 -I fuzz/test_ci.py`; the pull request's `fuzz.yml` run and the failing run of AC-4.

## Notes and pitfalls

- Seeds come from files in the repository, as today (`ci.py seeds`): valid messages and recordings built from the engine's tests or committed as small JSON files written for the purpose, and CRDT blobs made by editing a document in the target's seed generator or a test.
- The engine refuses messages above its limits (spec [§13](../../specs/engine-protocol.md#13-limits)); choose `-max_len` so that inputs can reach those limits where it matters, as the default-limits targets do for bayan-opc.
- The configuration must keep `test.allow_panic` off in `engine_messages`, `engine_tile` and `engine_replay`; otherwise `diag.panic` is a deliberate crash.
- Loro is large; building it with AddressSanitizer on the nightly takes time. Measure the build in the job and keep the cache of the build folder if the workflow has one.
- Whether Loro's crash findings reached its maintainers is still unconfirmed ([M12](../../plan/reviews/2026-10-27.md#m12-nothing-records-that-loros-crash-findings-reached-its-maintainers)). The private reports above keep `crdt_import` from publishing them again.
- CORE-011 also changes `fuzz/` (a target for the lab's scanner) and `fuzz.yml`'s path filter; the two work packages should not run at the same time.

## Escalate if

- `crdt_import` finds a panic or an abort in Loro that `import` does not contain, or a failure that keeps every nightly run red; propose whether to keep the target out of the nightly run until Loro is fixed or to add a guard in the adapter.
- The fuzz workspace would need a license or advisory exception that the main workspace does not already have.
- No private way to reproduce a nightly failure works well enough, so that keeping crash inputs private seems to need storage or encryption outside GitHub Actions.
