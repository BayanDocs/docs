# Developing bayan-core

[bayan-core](https://github.com/BayanDocs/bayan-core) is the engine of BayanDocs, a Rust workspace: the document model, file formats, layout, rendering, editing logic, collaboration and encryption, everything that must behave the same on desktop and web. It also hosts the Fidelity Lab (`lab/`), the fuzz targets (`fuzz/`) and time-boxed experiments (`spikes/`). This page is the setup map; the repository's [README.md](https://github.com/BayanDocs/bayan-core/blob/HEAD/README.md) and [AGENTS.md](https://github.com/BayanDocs/bayan-core/blob/HEAD/AGENTS.md) are the reference, in particular AGENTS.md's sections "Verification gate", "Engine artifacts" and "Toolchain". Start with [Getting started](getting-started.md) for the base tools and rustup.

## Platforms

Ubuntu 24.04, macOS on Apple Silicon and Windows on x64: CI runs the gate on all three for every pull request, every push to `main` and every night (`.github/workflows/verify.yml`: `ubuntu-24.04`, `macos-latest`, `windows-latest`). The setup script, `scripts/dev-setup.sh`, runs on Linux and macOS.

## What you need

- **Git, curl and a C linker**, from [step 1 of Getting started](getting-started.md#step-1-the-base-tools-for-your-system). The gate needs curl 7.87 or later, because bayan-lab's storage tests run it; macOS, Ubuntu 24.04 and up-to-date Windows 10 and 11 include one.
- **rustup** ([step 2](getting-started.md#step-2-rust)). In the repository it installs the toolchain that `rust-toolchain.toml` pins, with Clippy, rustfmt and two WebAssembly targets: `wasm32-unknown-unknown`, the target of the web app's engine, and `wasm32-wasip1`, on which the gate runs the tests a second time as WebAssembly.
- **Node.js**, at the version of `NODE_VERSION` in `xtask/src/verify.rs`: the gate runs the WebAssembly tests in it.
- **cargo-deny**, at the version of `CARGO_DENY_VERSION` in `xtask/src/verify.rs`: the gate's dependency audit.
- Only for the engine artifacts, which the gate does not build: **wasm-bindgen** for the WebAssembly package (`cargo xtask wasm-package`), **Miri** on a pinned nightly toolchain (`cargo xtask miri`), and on Windows a Visual Studio developer environment for the C driver (`cargo xtask c-driver`).

## Set up

### Linux and macOS

```sh
git clone https://github.com/BayanDocs/bayan-core.git
cd bayan-core
scripts/dev-setup.sh
```

The script installs the pinned toolchain with its targets, Node.js (checked against its SHA-256 and kept in `~/.local/share/bayandocs/core-tools`), wasm-bindgen and Miri; `scripts/dev-setup.sh --help` lists the options that leave some of them out. At the end it prints the `export PATH=…` line that puts its Node.js first on your `PATH`: add that line to your shell's profile.

Then install cargo-deny with the command that AGENTS.md gives in its section "Verification gate", `cargo install --locked cargo-deny@<version>`, where `<version>` is `CARGO_DENY_VERSION` in `xtask/src/verify.rs`. Run it inside the repository, so that rustup builds it with the pinned toolchain. If cargo-deny is missing or at another version, the gate stops and prints the exact command.

### Windows

In Git Bash:

```sh
git clone https://github.com/BayanDocs/bayan-core.git
cd bayan-core
rustup toolchain install
```

`rustup toolchain install`, run without a name inside the repository, installs the toolchain that `rust-toolchain.toml` pins, as the Windows job of `verify.yml` does. Install Node.js at the version of `NODE_VERSION` from [nodejs.org](https://nodejs.org) yourself (the setup script has no Windows build; CI downloads that release's `node.exe` and checks its SHA-256), and cargo-deny with the same `cargo install` command as above.

## Run the gate

```sh
cargo xtask verify
```

Run it from anywhere in the repository, before every push. A preflight first checks that the toolchain, cargo-deny and Node.js match their pins, and that no compiler flag or wrapper weakens the lint rules. Then the gate runs its steps in order and stops at the first failure: the supply-chain checks (every dependency pinned exactly, and every new package version in a `Cargo.lock` at least 24 hours old, which needs the full Git history), formatting, Clippy for the host and for WebAssembly, the tests natively and as WebAssembly in Node.js, the WebAssembly build, the documentation, cargo-deny, the guardrails (which prove the lint rules still reject what they must) and the determinism checks. Each step prints its command, so a failing step can be re-run by itself. The first run downloads and compiles every dependency, which takes a while and several gigabytes in `target/`.

CI runs the same command on the three systems, and more workflows besides: the engine artifacts (`artifacts.yml`: the C SDK on all three systems, the WebAssembly package, the drivers that check that every build renders the same tile, and Miri), fuzzing (`fuzz.yml`), the text pipeline spike (`text-pipeline.yml`), and the checks shared by every repository. [GitHub Settings Baseline](github-settings.md#rulesets) lists the checks that must pass.

## Deeper notes

- **Determinism.** Layout must give the same result on every platform, so the rules of [AGENTS.md §7](../AGENTS.md#7-determinism-core-repository) apply: integer layout units, no platform floating-point math, no output that depends on hash-map order. The gate enforces most of them with Clippy rules, the lint canary and the determinism step; bayan-core's AGENTS.md, section "Lint rules and exceptions", explains every rule and the narrow ways to make an exception.
- **The engine artifacts.** `cargo xtask sdk` builds the C SDK that bayan-desktop links, and `cargo xtask wasm-package` the WebAssembly package that bayan-web serves; AGENTS.md, section "Engine artifacts", gives the commands that test them. The shells build these from the bayan-core commit they pin, so a change to the engine reaches them only when they move their pin.
- **Fuzzing.** The fuzz targets in `fuzz/` are a separate Cargo workspace on a pinned nightly toolchain, run with cargo-fuzz; `fuzz/README.md` explains how to run them, and what to do with a failure (fuzzing failures stay private).
- **The Fidelity Lab.** The lab's tools are in `lab/`; [the Fidelity Lab specification](../specs/fidelity-lab.md) describes what they measure.
- **Pins.** Besides the ones named above, `scripts/dev-setup.sh` pins wasm-bindgen (equal to the wasm-bindgen crate in `Cargo.lock`) and the nightly toolchain for Miri. Every pin and how it moves is in the [dependency update runbook](dependency-update-runbook.md#bayan-core).
