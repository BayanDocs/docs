# CORE-012: The outside world, part 2 — the rest of the standard library, the build environment and exemptions per item

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | RELEASE / SECURITY |
| Repository | bayan-core (`xtask/`) |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | CORE-009 (both change the Clippy step of `xtask`: `verify.rs` and `dep_info.rs`) |
| Unblocks | — |
| Status | Ready |
| Requirements | ARC-08, FID-02 |
| Decisions | ADR-0005 (decision 5), ADR-0012 (decision 5), ADR-0017, ADR-0025 |
| Specs | — |

## Context

The engine never touches the outside world itself: no clock, no randomness, no environment, no files, no network, no processes (ADR-0012 decision 5, ADR-0005 decision 5, [plan/03 §12](../../plan/03-architecture.md#12-cross-cutting-rules)); it asks its host. FU-4 (bayan-core#39, merged as `3c5a18f`), the follow-up of the architecture review's finding [M5](../../plan/reviews/2026-10-27.md#m5-the-outside-world-rule-is-enforced-only-by-review-and-the-engine-already-reads-the-environment), made the gate enforce part of this:

- After its runs, the Clippy step reads the source text of every file that the compiler compiled into code that ships, as the compiler's dependency files list them, and fails if a crate that `OUTSIDE_WORLD` in `xtask/src/verify.rs` does not list names one of the five modules of `MODULES`, `std::env`, `std::fs`, `std::net`, `std::process` and `std::time`, or if a listed crate names a module that its entry does not list ([`xtask/src/outside_world.rs`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/xtask/src/outside_world.rs#L52)).
- `cargo xtask wasm-package` fails on any import of the engine's WebAssembly module that `WASM_IMPORTS` does not list.
- The engine's thread has a fixed stack size, so that `RUST_MIN_STACK` does not decide how deeply an input may nest ([thread.rs:173](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-engine/src/thread.rs#L173)).

FU-4's pull request named three follow-ups that this work package takes, each of size S. They are quoted here with what this planning session found on `3c5a18f`:

**1. Other ways out through the standard library** (FU-4's follow-up 3). "Outside the five modules, std still reaches the file system, the environment, the clock or the operating system's randomness in a few places that the check does not cover: the methods of `std::path::Path` that ask the file system (`exists`, `try_exists`, `is_file`, `is_dir`, `is_symlink`, `metadata`, `symlink_metadata`, `read_dir`, `read_link` and `canonicalize`), which a ban of `std::path` cannot cover, because bayan-opc's `compound_file.rs` uses `std::path::{Component, PathBuf}`; `std::hash::RandomState`, also reachable as `std::collections::hash_map::RandomState`, which seeds itself from the operating system; a thread started without an explicit stack size (`std::thread::spawn`, `std::thread::scope`, and `Builder::spawn` without `stack_size`) reads `RUST_MIN_STACK`; `std::thread::available_parallelism` reads files of the operating system; `std::thread::sleep`, `park_timeout`, `Receiver::recv_timeout` and `Condvar::wait_timeout` read the clock; `std::backtrace::Backtrace::capture` reads `RUST_BACKTRACE`; and `std::io::stdin`, `stdout` and `stderr` reach the console, where the print lints cover only the print macros, at a level that an assembled attribute can lower. Today the engine's shipped code uses none of them except `std::thread::Builder`, now with a stack size, and `std::thread::current`. A list of forbidden items next to `MODULES` would cover them. `std::os` needs no entry: its submodules are platform-specific, and code using them could not compile on all three systems without a platform condition, which the source check forbids." Checked: in the code that ships of the crates outside `OUTSIDE_WORLD`, the only such uses are `std::thread::Builder::new()…stack_size(…)` and `std::thread::current()` in bayan-engine's `thread.rs`; `recv_timeout` appears only in `crates/bayan-engine/src/thread/tests.rs`, a test module in a file of its own, which the compiler does not read for the code that ships. bayan-opc's [`compound_file.rs`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/crates/bayan-opc/src/compound_file.rs#L7) uses `std::path::{Component, PathBuf}` to build cfb's paths without touching the file system.

**2. The build environment** (FU-4's follow-up 4). "`env!` and `option_env!` read environment variables while the crate is compiled, not while the engine runs, so they are outside this check; today the engine's crates read only Cargo's `CARGO_PKG_VERSION` (for the version string). The compiler records each such read in its dependency files (`# env-dep:` lines), so the Clippy step could allow only Cargo's `CARGO_PKG_*` variables." Checked: `dep_info.rs` reads the dependency files but skips their `#` lines ([dep_info.rs:215](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/xtask/src/dep_info.rs#L215)). In a Clippy run for the host (dev profile), the units of workspace members record these reads, apart from Clippy's own `CLIPPY_ARGS` and `CLIPPY_CONF_DIR`: `CARGO_PKG_VERSION` in bayan-engine (`ENGINE_VERSION`) and bayan-ffi (its version string); `CARGO_MANIFEST_DIR`, `CARGO_BIN_EXE_bayan-cli`, `CARGO_BIN_EXE_bayan-lab` and `CARGO_TARGET_TMPDIR` in test units; and `CARGO_MANIFEST_DIR`, `CARGO_PKG_REPOSITORY` and `CARGO_PKG_VERSION` in xtask, which is on `OUTSIDE_WORLD`.

**3. Exemptions per item for bayan-ffi** (FU-4's follow-up 6). "bayan-ffi may use all of `std::process` and `std::time`, although it needs only `std::process::abort` and `std::time::Instant`. An entry that lists items instead of whole modules would keep `std::process::Command` and the wall clock (`SystemTime`) out of the binding too." Checked: bayan-ffi's code that ships uses exactly `std::time::Instant` and `std::process::abort` (its `tests.rs` also uses `Instant`, as a test).

## Objective

The gate rejects every route to the outside world that the standard library offers outside the five modules, every build-time read of an environment variable other than Cargo's `CARGO_PKG_*` in the code that ships, and every item of an exempted module that the exemption does not name.

## Scope

### In scope

- **Forbidden items.** A list next to `MODULES`, each entry with what it reaches and why it is forbidden, checked on the same text and with the same path model as the modules (whatever spaces, comments and raw identifiers stand between, also in `use` groups and renames): at least the items of follow-up 1. A method of `std::path::Path` is called on a value, not named by a path, so decide how to catch it without resolving types, and explain the choice: for example, forbid naming `Path` and `PathBuf` from `std::path` (and `std::ffi::OsStr`'s conversion to a path) in the code that ships except where an exemption names them for a crate, with bayan-opc's `compound_file.rs` exempted for `Component` and `PathBuf` and its use reviewed; or reject those method names after a `.` in the crates outside `OUTSIDE_WORLD`. A thread without a stack size can only be caught as "`std::thread::spawn`, `scope` and `Builder` are forbidden, except an approved use", so bayan-engine's `thread.rs` gets a narrow, reasoned exemption, or a helper in bayan-engine that always sets the size becomes the only allowed way to start a thread. Keep `std::thread::current`, which reads nothing outside.
- **Build-time environment.** After each Clippy run, read the `# env-dep:` lines of the dependency files of every unit of a workspace member, and fail on any variable other than Clippy's own two (`CLIPPY_ARGS` and `CLIPPY_CONF_DIR`) and Cargo's `CARGO_PKG_*`, in the units that are not tests of the members that `OUTSIDE_WORLD` does not exempt from `std::env`. Test units and the exempted members may read Cargo's other variables; decide whether they need a list too and explain the choice. The error names the run, the unit and the variable.
- **Exemptions per item.** An entry of `OUTSIDE_WORLD` may name items (`std::process::abort`, `std::time::Instant`) instead of whole modules; give bayan-ffi exactly those two, and keep the check that an exemption cannot go stale (an item that the crate no longer uses fails, as a module does today). Decide whether the other entries (the tools, the spikes, bayan-lab and xtask) stay at the level of modules, and say so in their reasons.
- **Tests** in xtask for every forbidden item (named directly, through `use`, through a group, through a rename), for the environment check (a recorded dependency file with `option_env!("HOME")` fails; `CARGO_PKG_VERSION` passes; a test unit with `CARGO_MANIFEST_DIR` passes) and for an item-level exemption (`std::process::Command` in bayan-ffi fails; `std::process::abort` passes).
- **Documentation**: the limits listed in `outside_world.rs`, bayan-core's `AGENTS.md` ("No outside world" and "Lint rules and exceptions", which today lists the `Path` methods and `RandomState` as things the check does not see) and the doc comments of `verify.rs`.

### Out of scope

- Dependencies' own calls to the outside world (cfb's `web-time`, Loro's randomness and clock, which ADR-0012's amendment of 2026-10-08 accepts); the WebAssembly import check already sees them in the browser.
- The lint attributes that macros assemble (CORE-009).
- Changing what the engine does: this work package only checks; if a forbidden item turns out to be in use, stop and ask (below).

## Deliverables

- Changes to `xtask/src/outside_world.rs`, `xtask/src/dep_info.rs` and `xtask/src/verify.rs`, with tests.
- The documentation above.

## Acceptance criteria

- [ ] AC-1 Each item of follow-up 1 that is not exempted fails the gate when written into the code that ships of bayan-units (output for a sample of at least `RandomState`, `std::thread::spawn`, `std::thread::sleep`, `std::io::stdout` and a file-system method of `Path`), and passes in a test module in a file of its own.
- [ ] AC-2 `option_env!("HOME")` (or `env!` of any variable other than `CARGO_PKG_*`) in the code that ships of bayan-engine fails the Clippy step, naming the variable; the same in an integration test passes.
- [ ] AC-3 `std::process::Command` and `std::time::SystemTime` in bayan-ffi's code that ships fail; its `abort` and `Instant` pass; an item listed for bayan-ffi that the crate no longer uses fails.
- [ ] AC-4 `cargo xtask verify` passes on the change, and every exemption added is listed in the pull request with its reason.
- [ ] AC-5 The documentation no longer lists as unseen what the check now sees, and lists what it still does not see.

## Verification

`cargo xtask verify`; `cargo test -p xtask`; the experiments of AC-1 to AC-3, each shown failing and then reverted.

## Notes and pitfalls

- The check models paths and does not resolve names (`outside_world.rs` explains its limits), so it cannot tell `Path::exists` from a method of the same name on another type; any rule on method names must be justified by what it catches and what it costs in false alarms.
- `std::collections::hash_map::RandomState` is the same type as `std::hash::RandomState`; `HashMap::new` uses it too, but `clippy::disallowed_types` already forbids the hash collections (and CORE-009 keeps that ban from being lowered).
- Clippy records `CLIPPY_ARGS` with the arguments of each run, so CORE-009's audit runs change that line; the environment check must accept Clippy's own variables in every run.
- Cargo sets more variables than `CARGO_PKG_*` (`CARGO_MANIFEST_DIR`, `CARGO_CRATE_NAME`, `OUT_DIR` with a build script); the code that ships of the engine's crates needs none of them today.

## Escalate if

- Code that ships uses a forbidden item that cannot simply move to a test or to the host; that is a change to the engine, which needs its own decision.
- Catching `Path`'s methods would need resolving types, so that only review can cover them; propose what to document instead.
