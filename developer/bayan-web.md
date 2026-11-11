# Developing bayan-web

[bayan-web](https://github.com/BayanDocs/bayan-web) is the browser app of BayanDocs, written in TypeScript with React and Vite: a thin shell that runs bayan-core's engine, compiled to WebAssembly, in a Web Worker, and provides the interface, the compositor that draws the engine's page tiles, the input bridges and the accessibility mirror. This page is the setup map; the repository's [README.md](https://github.com/BayanDocs/bayan-web/blob/HEAD/README.md) and [AGENTS.md](https://github.com/BayanDocs/bayan-web/blob/HEAD/AGENTS.md) are the reference, in particular the README's "Getting started" and AGENTS.md's sections "Setup", "Verification gate" and "Dependency mechanisms". Start with [Getting started](getting-started.md) for the base tools and rustup.

## Platforms

Ubuntu 24.04 on x86-64, and macOS 14 or later on Apple Silicon or Intel. CI runs the gate on Ubuntu 24.04, on macOS 15 with Apple Silicon and on macOS 26 with Intel (`.github/workflows/ci.yml`: `ubuntu-24.04`, `macos-15`, `macos-26-intel`). Windows and other systems are not supported: the setup script stops where it has no pinned download for the machine.

## What you need

- **Git**, and on Ubuntu **curl** and **unzip**, from [step 1 of Getting started](getting-started.md#step-1-the-base-tools-for-your-system); on macOS, the Xcode command line tools.
- **rustup** ([step 2](getting-started.md#step-2-rust)), and the C linker from step 1: the engine is built with bayan-core's own pinned toolchain.
- **`sudo`** on Ubuntu, once: the setup script installs the Ubuntu packages that the test browsers need.

Everything else (Node.js, pnpm, the project's packages and the browsers for the end-to-end tests) is installed by the setup script, at pinned versions.

## Set up

```sh
git clone https://github.com/BayanDocs/bayan-web.git
cd bayan-web
scripts/dev-setup.sh
scripts/engine-package.sh
```

`scripts/dev-setup.sh` installs, each checked against a pinned hash:

- **Node.js**, at the version in `.nvmrc`;
- **pnpm**, as its native binary, at the version in the `packageManager` field of `package.json`, checked against the SHA-512 that `pnpm-lock.yaml` records for it (Corepack is not used);
- **the project's packages**, with `pnpm install --frozen-lockfile`, which fails if `pnpm-lock.yaml` does not match `package.json` and never runs a package's install script;
- **the browser builds** that the end-to-end tests run in (Chromium's headless shell, Firefox and WebKit): Playwright names the builds your machine needs, and the script refuses any build that it has no pinned hash for;
- on **Ubuntu**, the **browsers' system libraries**, from the Ubuntu archive frozen at a snapshot date (the reason for `sudo`). On macOS the browsers go to `~/Library/Caches/ms-playwright`, and nothing needs `sudo`.

When the script puts Node.js or pnpm in its own folder, it prints the `export PATH=…` line to add to your shell's profile. Run it again whenever it changes.

`scripts/engine-package.sh` builds the engine's WebAssembly package into `engine-package/`, which the development server, the build and the tests need. Until bayan-core publishes releases, the app builds the engine from the bayan-core commit named in `bayan-core.pin`: the script clones bayan-core into `~/.cache/bayandocs/bayan-core`, checks that the commit is on bayan-core's `main` and reached it at least 24 hours before it was pinned (which reads this repository's history, so it refuses a shallow clone), installs bayan-core's pinned toolchain and wasm-bindgen with bayan-core's own setup script, and builds the package. Run it again whenever `bayan-core.pin` changes; the gate fails while `engine-package/` was built from another commit.

## Run the gate

```sh
pnpm verify
```

Run it before every push. In order, it checks the dependency policy (exact pins and pnpm's safety settings), where every locked package comes from (`pnpm-lock.yaml` may name only the npm registry, each package with a SHA-512 hash), and that `engine-package/` was built from the pinned commit; then it lints with Biome, type-checks, runs the unit tests (Vitest), builds the app (with integrity hashes for every script, the licence notices of the bundled packages and a size report with budgets), runs the end-to-end tests and measurements in Chromium, Firefox and WebKit (Playwright), and runs the audit, which fails on any high or critical security advisory.

CI (`.github/workflows/ci.yml`) builds the engine package once, on Ubuntu, and runs `scripts/dev-setup.sh` and `pnpm verify` with it on the three systems; then come the checks shared by every repository. [GitHub Settings Baseline](github-settings.md#rulesets) lists the checks that must pass.

## Deeper notes

- **Everyday commands.** `pnpm dev` starts the development server at `http://localhost:5173`, `pnpm build` builds the production app into `dist/`, `pnpm preview` serves `dist/` at `http://localhost:4173`, and `pnpm format` formats the code. Both servers send the same security headers as production (the README's table notes the one exception).
- **pnpm only.** Never use npm or Yarn in this repository, and ignore pnpm's notice that an update is available: the pinned pnpm moves only in the monthly dependency session. Installing or upgrading a package follows the strict rules of [ADR-0017](../adr/0017-supply-chain-and-dependency-policy.md), which pnpm's own settings and the gate's checks enforce: exact versions, a 24-hour minimum age, no install scripts, and a justification for every new dependency. AGENTS.md, section "Dependency mechanisms", explains each setting.
- **The engine pin** moves only in a pull request of its own, which says what changed in bayan-core between the two commits (bayan-web's AGENTS.md).
- **Security of the app.** The app runs under a strict Content Security Policy with Trusted Types, and every script it loads carries a Subresource Integrity hash. AGENTS.md explains the rules that keep them working, such as the single Trusted Types policy and how the engine's worker is started.
- **Pins.** Node.js in `.nvmrc`, pnpm in `package.json`, the packages in `pnpm-lock.yaml`, the engine in `bayan-core.pin`, and the browsers and the Ubuntu snapshot in `scripts/dev-setup.sh`. Every pin and how it moves is in the [dependency update runbook](dependency-update-runbook.md#bayan-web).
