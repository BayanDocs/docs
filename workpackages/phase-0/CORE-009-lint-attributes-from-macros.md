# CORE-009: Lint exceptions that nobody wrote — check what the compiler silenced

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | RELEASE / SECURITY |
| Repository | bayan-core (`xtask/`) |
| Attach to session | bayan-core, docs |
| Size | M |
| Depends on | CORE-001 |
| Unblocks | CORE-012 (both change the Clippy step of `xtask`); reviews no longer need to check every macro that takes a `#` or a bracket group as a `tt` |
| Status | Ready |
| Requirements | FID-02, SEC-01 |
| Decisions | ADR-0005, ADR-0006, ADR-0017, ADR-0025 |
| Specs | — |

## Context

**Words used here.** A *lint* is a rule that the Rust compiler or Clippy (Rust's extra linter) checks, such as "no `HashMap`" or "no `unwrap()`". Each lint has a *level*: `allow` (off), `warn`, `deny` (an error) or `forbid` (an error that no code can switch off again). An *attribute* such as `#[expect(clippy::disallowed_types, reason = "…")]` changes the level for the item it is written on. A *macro* is code that writes code; a `macro_rules!` macro can take single tokens (`tt`, "token tree") from its caller and put them together in a new order.

**How bayan-core's gate handles lint levels today.** The workspace sets its lints in the root `Cargo.toml` ([`[workspace.lints]`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/Cargo.toml#L73)), and `cargo xtask verify` runs Clippy four times with every warning an error (`-D warnings`; [`clippy_args`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/xtask/src/verify.rs#L516)). The only sanctioned exception is `#[expect(lint, reason = "…")]` on the smallest item that needs it: Clippy's `allow_attributes` and `allow_attributes_without_reason` lints reject `#[allow]` and exceptions without a reason, and an `#[expect]` that is no longer needed fails. The lints set to `forbid` (`clippy::disallowed_methods`, the float bans of ADR-0005 §4, and `unsafe_code` outside bayan-ffi and bayan-wasm) cannot be lowered at all (error E0453). Two later changes made the gate read the compiler's own record instead of trusting a model of it: bayan-core#38 (`9d6ed5b`) checks that the compiler read no file the source check did not read ([`dep_info.rs`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/xtask/src/dep_info.rs)), and FU-4 (bayan-core#39, `3c5a18f`) added a check of the source text of the code that ships ([`outside_world.rs`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/xtask/src/outside_world.rs)) precisely because a lint can be lowered.

**The hole.** A lint exception can reach the compiler without anyone writing it out, and then neither the preflight's source check nor Clippy notices it. bayan-core#38's follow-up 3 describes the first two forms; this planning session found the third and checked all three on today's `main`:

1. **A split `#[allow]`.** This code, added to bayan-units' `src/lib.rs`, builds `#[allow(clippy::disallowed_types)]` from the `#` of a doc attribute and a bracket group handed in separately, so the `HashMap` below it is never reported:

   ```rust
   macro_rules! exempt { ($hash:tt $decoy:tt, $bracket:tt) => { $hash $bracket /// The number of entries of an empty map.
   #[must_use] pub fn entries() -> usize { let map: std::collections::HashMap<u8, u8> = std::collections::HashMap::new(); map.len() } }; }
   exempt!(#[doc = "Entries."], [allow(clippy::disallowed_types)]);
   ```

2. **A split `#[expect]`:** the same with `[expect(clippy::disallowed_types, reason = "…")]` as the bracket group.
3. **An `#[allow]` written out in full inside another crate's macro.** Clippy's `allow_attributes` lint does not report an attribute that a macro of another crate puts out, and the preflight does not look at lint attributes, so this passes too (std's `thread_local!` is used in bayan-engine and bayan-ffi):

   ```rust
   std::thread_local! {
       /// A map under an `#[allow]` written in full, which std's macro re-emits.
       #[allow(clippy::disallowed_types)]
       static MAP: core::cell::RefCell<std::collections::HashMap<u8, u8>> = core::cell::RefCell::new(std::collections::HashMap::new());
   }
   ```

On `3c5a18f`, with forms 1 and 2 in bayan-units' `src/lib.rs`, `cargo xtask verify` passes the preflight, the supply-chain and formatting steps, all four Clippy runs with their file comparisons, and the outside-world check, and moves on to the tests. Form 3 passes `cargo clippy -p bayan-units --all-targets --all-features --locked -- -D warnings`, the gate's Clippy command for that crate. Every lint that is not set to `forbid` can be lowered this way: the hash-map ban of ADR-0005 §5 (`clippy::disallowed_types`, `iter_over_hash_type`), `unwrap_used`, `print_stdout` and `print_stderr`, `exit`, the numeric cast lints, `missing_docs`, `unsafe_op_in_unsafe_fn`, and in bayan-ffi and bayan-wasm, whose own lint tables only deny it, `unsafe_code`. Until a check closes this, [bayan-core's AGENTS.md](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/AGENTS.md#L122) and [`sources.rs`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/xtask/src/sources.rs#L26) ask reviewers to check every macro that takes a `#` or a bracket group as a `tt`; form 3 needs no such macro.

**The approaches, compared.** This session tried each on `3c5a18f` with the pinned toolchain (Rust 1.99.0) and nightly (`nightly-2026-10-02`).

| | A. The compiler's record of what it silenced (recommended) | B. The compiler's printout of the expanded code | C. More source rules | D. Raise the lints to `forbid` |
|---|---|---|---|---|
| How | Extra Clippy runs pass `--force-warn <lint>` for every guarded lint. A force-warned lint is reported wherever it occurs, also where an attribute set it to `allow` or `expect`. Every occurrence reported must lie inside an `#[expect(<lint>, reason = "…")]` written out in full in the source. | Print the code after macro expansion (`-Zunpretty=expanded` or `-Zunpretty=hir`) and compare the lint attributes in it with those written in the source. | Reject the `tt` fragment in the workspace's `macro_rules!` (none uses it today outside the test strings of xtask), or list each such macro in a reviewed list. | Set every guarded lint to `forbid`. |
| Catches forms 1 and 2 | Yes: the run reports both `HashMap`s, at the macro's line. | Yes: the printout shows `#[allow(clippy::disallowed_types)]` before `entries`. | Yes, for macros of the workspace. | Yes. |
| Catches form 3, and attributes from dependencies' procedural macros | Yes: it reports the map in `thread_local!`. | Form 3 yes; a derive's own attributes need a reviewed list of exact texts. | No. | Yes. |
| Toolchain and gate rules | Stable: `--force-warn` works on Rust 1.99.0 through `cargo clippy -- …`. The preflight rejects it only in `RUSTFLAGS` and `.cargo/config.toml` ([`flags.rs`](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/xtask/src/flags.rs#L46)), where it could weaken the gate's own runs; xtask passes it itself, after `--`, in runs of its own. | Needs `-Z`: the pinned nightly, or `RUSTC_BOOTSTRAP=1` with the stable compiler, both of which the preflight forbids for the gate's builds; the nightly is a different compiler from the one that ships, and CI installs it only on Linux, for Miri and fuzzing. | Nothing new. | Nothing new. |
| Stability | `--force-warn` and Cargo's JSON messages are stable interfaces. | The printout's format is unstable and changes with every toolchain, which the monthly dependency session would have to follow. | A model of the compiler, like the preflight's split-form rules, which have already needed three rounds. | Stable. |
| What it cannot see | Attributes that change linting without setting a level, such as `#[automatically_derived]` or `#[clippy::msrv]`; code that a lint's own implementation skips. | Where an attribute came from: the printout has no source positions, so an attribute written once in a macro appears once per call, and comparison works only by text and count. | Every form a future macro or compiler version adds. | Nothing, but see the next row. |
| Cost | 4 more Clippy runs over the workspace's members (dependencies are not checked again); on the planning session's machine the host run took 75 s and the WebAssembly run 52 s, each including the first check of the dependencies for its target. A conservative model in xtask of which item an attribute covers. | 8 printouts (each run with and without `test`), a parser for them, and a reviewed list of the attributes that serde, schemars and wasm-bindgen put out. | About 100 lines in `sources.rs`. | None, but it removes the sanctioned exceptions, such as `print_stdout` in the tools, the 117 uses of `unsafe_code` that bayan-ffi marks with `#[expect]`, and the numeric casts with a reason; so it works only for lints without exceptions. |

**What approach A finds on `main` today.** With every lint and group of the workspace's lint tables force-warned, the host run (dev profile) and the WebAssembly run (dev profile) report 209 distinct occurrences that attributes silence, and none comes from a macro expansion, also not from the procedural macros of serde, schemars or wasm-bindgen. A rough check finds a written `#[expect]` naming the lint for every one: in 138 cases earlier in the occurrence's own file, in 43 the crate-level `#![expect(clippy::print_stdout, clippy::print_stderr, …)]` of xtask's `main.rs`, and in 28 bayan-ffi's `#[expect(unsafe_code, …)]` on its `mod tests;` declaration. With the three forms above in bayan-units, a force-warned Clippy run of that crate reports six occurrences, two for each form, that no written `#[expect]` covers. Facts checked on Rust 1.99.0: a force-warned occurrence is a warning that ignores `-D warnings` (the compiler says so: "the `clippy::disallowed_types` lint ignores `-D warnings`"), so the build still succeeds and xtask must read the messages and fail itself; a lint set to `forbid` stays an error, and E0453 still fires; and an occurrence under a written `#[expect]` still fulfils it, so no `unfulfilled_lint_expectations` error appears.

## Objective

The gate fails whenever a lint of the workspace is silenced by anything other than an `#[expect(lint, reason = "…")]` written out in full in the source, whatever wrote the attribute: a macro of the workspace, a macro of another crate or a procedural macro. Approach A is the recommended way.

## Scope

### In scope

- **Audit runs.** After the four Clippy runs, four more, one for each entry of `CLIPPY_RUNS`, with the same targets and profiles and `--force-warn` for every guarded lint passed after `--`. They collect the occurrences from Cargo's JSON messages (each message's lint code and primary span, and its expansion chain for the error message); they enforce nothing by their exit status. Keep the existing four runs exactly as they are, so that the compiler stays the first line of enforcement and a mistake in the new check can only miss an exception, never accept a plain `HashMap`.
- **Guarded lints.** Every lint and lint group that the workspace's lint tables set to `warn` or `deny`: `[workspace.lints]` in the root `Cargo.toml` and the copies in bayan-ffi's and bayan-wasm's manifests, read from the manifests by xtask (with `toml_subset.rs`) so that a lint added later is guarded from the same commit. Lints set to `forbid` need nothing. A group such as `clippy::all` also force-warns its members that the workspace sets to `allow` (today `manual_clamp`); ignore occurrences of lints whose level in the crate is `allow`.
- **Coverage.** An occurrence passes only if an attribute written out in full in the source text covers its primary span: `#[expect(<lint>, reason = "…")]` or `#![expect(<lint>, reason = "…")]`, also inside a `cfg_attr` with an approved condition, naming exactly that lint (not a group that contains it). The model may be stricter than the compiler, never looser: an outer attribute covers the item, statement, field, match arm or expression that follows it, ending no later than its first `;` or `,` at the same depth, the end of its first `{…}` group, or the end of the group around it; an outer attribute on `mod name;` covers that module's file and its submodules' files; an inner attribute covers the rest of the block, module or file it stands in, and in a crate's root file the whole crate. An occurrence whose primary span lies outside the files the source check read fails, naming the macro from its expansion chain.
- **Failing loudly.** The audit fails on any message it cannot read, a member without a unit, a run that did not finish, and a guarded lint list that comes out empty. Its error names the run, the lint, the file and line, and says that no `#[expect]` written out in full covers it.
- **Tests.** Unit tests for the coverage model and the message reading, with recorded JSON messages and source snippets: the three forms of the context fail, and the sanctioned forms pass (an `#[expect]` on a function, a statement, a field, a match arm, a `mod name;` declaration, a crate-level `#![expect]`, one inside `cfg_attr(test, …)`, and one written in full inside a macro's own code next to the item it covers). The lint canary (`xtask/lint-canary`) gains the three forms as cases that the gate must reject.
- **Documentation.** bayan-core's `AGENTS.md` ("Verification gate", step 3, and "Lint rules and exceptions": replace the reviewers' instruction with the new check and its limits), the known-limitation comment of `sources.rs`, and the doc comment of `clippy_step`.

### Out of scope

- Approaches B, C and D. The preflight's existing split-form rules stay (gates are never weakened, ADR-0025).
- Attributes that are not lint levels, such as `#[automatically_derived]`; record them as a follow-up if the work shows they matter.
- Changing any lint's level or the exception policy.
- The rest of the outside world (CORE-012).

## Deliverables

- `xtask/src/` (a module for the audit, and changes to `verify.rs` and, where needed, `dep_info.rs` and `json.rs`), with tests.
- Three new cases in `xtask/lint-canary/`.
- Documentation as above.

## Acceptance criteria

- [ ] AC-1 **Before:** on the change's merge base, the three forms of the context, added to bayan-units' `src/lib.rs`, pass the preflight and the Clippy step of `cargo xtask verify` (output in the pull request). **After:** on the change, `cargo xtask verify` fails at the Clippy step on each of them, naming the lint, the file and the line (output for each).
- [ ] AC-2 `cargo xtask verify` passes on the change itself; the pull request lists any `#[expect]` that had to move onto a smaller item, with the reason.
- [ ] AC-3 The unit tests and the lint canary cases of "Tests" pass, and each canary case passes the compiler and Clippy without the audit (a local experiment, output), so that it really exercises the gap.
- [ ] AC-4 A test fails if a lint set to `warn` or `deny` in any lint table is not force-warned, and the audit fails when the list is empty.
- [ ] AC-5 The four existing Clippy runs keep their arguments (the diff of `clippy_args` shows it), and no `--force-warn` reaches `RUSTFLAGS` or `.cargo/config.toml`; the preflight's rejection of those stays.
- [ ] AC-6 The time the audit runs add on each of CI's three systems is reported from the pull request's CI run, and the verify job stays within its time limit (raising the limit is allowed and must be explained).
- [ ] AC-7 The documentation names what the check does not see (attributes that are not lint levels, and code that a lint's own implementation skips).

## Verification

`cargo xtask verify`; the before and after runs of AC-1 with the three forms in bayan-units' `src/lib.rs`; `cargo test -p xtask`; the CI run of the pull request on Linux, Windows and macOS.

## Notes and pitfalls

- The guarded set must come from the manifests, not from a list kept by hand; otherwise the next lint added to `[workspace.lints]` is unguarded.
- Clippy writes the arguments it was given into each unit's dependency file (`# env-dep:CLIPPY_ARGS=…`), so switching between the normal and the audit arguments recompiles the members, not the dependencies. If the audit runs share the build folder with the normal runs, make sure `dep_info.rs`'s freshness check still holds for the units each run compiles; a separate build folder costs a second check of every dependency.
- A primary span points where the offending token is written: into a macro's own code for tokens the macro writes, or to the call for tokens handed in. An `#[expect]` written around a macro call does not cover tokens that the macro's own code writes; the coverage model rejects that case, and the fix is an `#[expect]` next to the item inside the macro.
- Clippy reports each occurrence once per unit (the library and its test build), sometimes for two tokens of one expression; deduplicate by lint, file, line and column.
- xtask uses only the standard library (ADR-0017); read the messages with its own `json.rs`.
- Never stop force-warning a lint to make the audit pass. A false positive means the `#[expect]` moves onto the item it covers.
- The measurements in the context come from one machine; the CI times of AC-6 are the ones that count.

## Escalate if

- A dependency's macro or procedural macro produces occurrences that no `#[expect]` in the workspace can cover, so that passing would need an exemption for code the workspace does not control.
- The audit runs would push the verify job past a reasonable time limit, so that merging `--force-warn` into the normal runs (which moves the enforcement of those lints from the compiler into xtask) looks necessary.
- `--force-warn` behaves differently on Windows or macOS than on Linux, or a future toolchain stops reporting force-warned occurrences under `#[expect]`.
