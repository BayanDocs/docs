# Developing bayan-server

[bayan-server](https://github.com/BayanDocs/bayan-server) is the zero-knowledge collaboration server, a Rust workspace: accounts, devices, sharing and a relay that stores and forwards end-to-end-encrypted data it can never read. It ships as a single binary in a single container. This page is the setup map; the repository's [README.md](https://github.com/BayanDocs/bayan-server/blob/HEAD/README.md) and [AGENTS.md](https://github.com/BayanDocs/bayan-server/blob/HEAD/AGENTS.md) are the reference, in particular AGENTS.md's sections "Verification gate" and "Working in this repository". Start with [Getting started](getting-started.md) for the base tools and rustup.

## Platforms

Linux on x86-64. CI runs every job on Ubuntu 24.04 (`.github/workflows/ci.yml`), and `scripts/dev-setup.sh` refuses to run on any other system.

## What you need

- **Git, curl, unzip and a C compiler and linker**, from [step 1 of Getting started](getting-started.md#step-1-the-base-tools-for-your-system). The C compiler builds SQLite, which the server embeds and compiles from its C source.
- **rustup** ([step 2](getting-started.md#step-2-rust)). In the repository it installs the toolchain that `rust-toolchain.toml` pins, with the WebAssembly target of the MLS spike.
- The tools that `scripts/dev-setup.sh` installs: **cargo-deny** for the gate, **grype** for scanning the container image, and the MLS spike's WebAssembly test tools (wasm-bindgen, Node.js, Chromium's headless shell and chromedriver).
- Only for the checks outside the gate: **Docker** to build and test the container image and to run a throwaway PostgreSQL server, and **`python3` and `psql`** for `cargo xtask sqlx-prepare`.

## Set up

```sh
git clone https://github.com/BayanDocs/bayan-server.git
cd bayan-server
scripts/dev-setup.sh
```

The script installs every tool at its pinned version and checks every download against its SHA-256: cargo-deny and grype into `~/.local/bin`, and the MLS spike's tools into their own folders under `~/.local/share/bayandocs/server-tools`, off your `PATH`, where the `cargo xtask mls-spike-*` commands find them. `scripts/dev-setup.sh cargo-deny` installs only what the gate needs. If `~/.local/bin` is not on your `PATH`, the script says so: add it in your shell's profile (Ubuntu's default profile adds it at login once the folder exists).

## Run the gate

```sh
cargo xtask verify
```

Run it before every push. It runs the supply-chain checks first (every dependency pinned exactly, and every new package version in a `Cargo.lock` at least 24 hours old, which needs the full Git history), so that no code of a rejected dependency is ever compiled; then formatting, Clippy with warnings as errors, the tests, the documentation and cargo-deny; then the same steps for the MLS spike's workspace (`spikes/mls`). The first run compiles every dependency, which takes a while and several gigabytes in `target/`.

CI (`.github/workflows/ci.yml`) runs the gate and also:

- **PostgreSQL integration:** `cargo xtask test-postgres` (the server with PostgreSQL, and a check that both databases' migrations create the same schema) and `cargo xtask sqlx-prepare --check` (the committed query metadata matches the migrations and queries);
- **the container image:** its build, `scripts/container-smoke-test.sh` (read-only root filesystem, non-root user, health check, clean shutdown) and grype's vulnerability scan;
- **the MLS spike in WebAssembly:** `cargo xtask mls-spike-wasm`, in Node.js and in headless Chromium;

and the checks shared by every repository. [GitHub Settings Baseline](github-settings.md#rulesets) lists the checks that must pass. Run the extra ones locally when your change touches what they check.

## Deeper notes

- **SQLite needs no setup.** It is the default database, built into the server. `cargo run -p bayan-server` runs the server on `127.0.0.1:8080` with its database in `./data`. Builds never need a running database: the query metadata that sqlx checks at compile time is committed in `crates/bayan-db-*/.sqlx/`, and `.cargo/config.toml` makes builds use it.
- **PostgreSQL** is the database for larger deployments. To run its tests or change a query or migration, start a throwaway server with the pinned image (the exact `docker run` command is in AGENTS.md, under "Database changes"), then run `cargo xtask test-postgres` with `BAYAN_TEST_POSTGRES_URL`, or `cargo xtask sqlx-prepare` with `BAYAN_SQLX_POSTGRES_URL`, as AGENTS.md shows. Every database change needs a migration in both database crates; AGENTS.md explains the rules that the tests check.
- **The container.** `docker build -t bayan-server .` builds the image, and `scripts/container-smoke-test.sh bayan-server` checks it; `docker compose up --build` runs it for development, with `--profile postgres` for a PostgreSQL setup. The README's quick start shows a hardened `docker run`, and the repository's `docs/deployment.md` and `docs/configuration.md` cover deployment and every setting. The final image is built `FROM scratch` and may contain only files whose licenses are on the allowlist; the smoke test fails on any other file.
- **The MLS spike** (`spikes/mls`, work package [SRV-002](../workpackages/phase-0/SRV-002-spike-mls.md)) is an experiment that is never part of the server. Its tests in headless Chromium need the libraries that Chromium uses, which GitHub's Ubuntu runners have; on a bare Ubuntu installation, bayan-web's `scripts/dev-setup.sh` lists them.
- **Pins.** The Rust toolchain is pinned in `rust-toolchain.toml`, and the builder image in `Dockerfile` must use the same Rust version; the PostgreSQL image is pinned by digest in `compose.yaml`, the CI workflow and AGENTS.md; every other tool in `scripts/dev-setup.sh`. Every pin and how it moves is in the [dependency update runbook](dependency-update-runbook.md#bayan-server).
