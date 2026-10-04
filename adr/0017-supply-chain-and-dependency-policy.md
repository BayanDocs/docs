# ADR-0017: Supply-chain and dependency policy

- **Status:** Accepted (owner preferences, encoded)
- **Date:** 2026-10-03
- **Deciders:** Owner (policy), Planner (mechanisms)
- **Related:** SEC-05, SEC-06, [AGENTS.md §5](../AGENTS.md#5-dependencies-strict--see-adr-0017), [plan/06 — monthly update session](../plan/06-agent-workflow.md#monthly-dependency-update-session), X-002, X-003

## Context

The owner's standing preferences for every repository:

- No automated version-update bots (no `.github/dependabot.yml`, no Renovate, no equivalent).
- GitHub Dependabot **security alerts** stay enabled as a repository setting (alerts only, no pull requests).
- Dependencies are updated in **batched agent-run sessions**, roughly monthly or immediately when a security alert fires: bump everything, run the full verification gate, fix what breaks, land one green pull request that explains the changes.
- **Every dependency version must be at least 24 hours old** before it is installed; never update a pinned dependency to a version younger than 24 hours.
- Keep passive fences wherever they exist: exact-pinned versions, committed lockfiles, `ignore-scripts=true`, audit and lockfile-lint gates in CI.
- If a repository documents its dependency posture, update that document in the same pull request as any posture change.

A recent incident shows why the age rule matters: on 2026-08-20 a compromised release of the Rust crate `arrayref` (0.3.10) was published with a dependency whose build script executed malicious code; it was removed about 86 minutes later, after 2,285 downloads (RUSTSEC-2026-0260). Cargo cannot disable build scripts, so a 24-hour minimum age is the defense that would have kept it out.

Tool capabilities verified on 2026-10-03:

- **pnpm** has `minimumReleaseAge` (minutes; 1440 is the default since pnpm 11) with a strict mode, and `pnpm install --frozen-lockfile` **re-checks** locked versions and fails on too-young ones. Since pnpm 10 dependency build scripts do not run by default; pnpm 11 replaced the old allowlist settings with `allowBuilds`, made `strictDepBuilds` the default, and blocks exotic sub-dependencies by default. `trustPolicy: no-downgrade` fails installs when a version has weaker provenance than earlier releases. The current major is pnpm 12.
- **Cargo** gains a native setting, `[registry] global-min-publish-age`, in **Rust 1.100 (2026-11-12)**; earlier stable releases ignore it. Cargo does **not** re-check versions already in `Cargo.lock`. The crates.io index carries a publish time (`pubtime`) per version, and the API exposes `created_at`.
- **lockfile-lint** supports npm and Yarn lockfiles only, not pnpm's.
- **vcpkg** pins exactly with `builtin-baseline` plus `overrides`; neither vcpkg nor Conan has a release-age gate. **aqtinstall** (for installing pinned Qt in CI) verifies SHA-256 checksums from the official Qt download site.
- **GitHub** offers a setting to require Actions pinned to full commit SHAs (since 2025-08-15), immutable releases (generally available since 2025-10-28) and artifact attestations. **zizmor** lints workflows (and flags unpinned or known-vulnerable actions); **pinact** pins actions and can verify a minimum age.
- Dependabot alerts can be enabled without version updates or security-update pull requests; it does not alert on SHA-pinned actions, which zizmor's known-vulnerable-actions audit covers.

## Decision

### Policy (all repositories)

1. **No update bots, ever.** CI fails if `.github/dependabot.yml`, `renovate.json` or similar configuration appears (X-003 adds this check).
2. **Dependabot alerts on** (including malware alerts); **Dependabot security updates off**; secret scanning and push protection on.
3. **Batched updates** only in the monthly dependency session or a security-alert session, using the prompts in [plan/06](../plan/06-agent-workflow.md#monthly-dependency-update-session). One green pull request per repository per session.
4. **24-hour minimum age** for every package, toolchain, CI action and tool version, enforced by tooling wherever possible (below) and stated in the pull request otherwise. If a security fix is younger than 24 hours, mitigate (disable the affected feature, pin an unaffected version) and update once it is eligible.
5. **Exact pins and committed lockfiles.** Builds use `--locked` / `--frozen-lockfile`.
6. **Install scripts disabled**; any exception is named in an allowlist with a justification.
7. **Audit and lockfile-integrity gates** run on every pull request and nightly.
8. **License allowlist:** MIT, MIT-0, Apache-2.0 (including the LLVM exception), BSD-2-Clause, BSD-3-Clause, ISC, Zlib, 0BSD, BSL-1.0, CC0-1.0, Unicode-3.0, Unicode-DFS-2016, MPL-2.0. Fonts and data packs may also use OFL-1.1, the GUST Font License, CC BY 4.0 and LGPL with font exceptions. Qt is used under LGPL-3.0 (dynamic linking). Anything else requires an ADR amendment. Dual-licensed packages qualify if one option is on the list. Copyleft dependencies (GPL, AGPL, and LGPL other than Qt) stay excluded even though our own code is GPL or AGPL: they could not be used in the Apache-2.0 areas and would block the proposed app-store permission (ADR-0003).
9. **Minimal dependencies.** Every new dependency is justified in its pull request (purpose, alternatives, license, maintenance, publish date, transitive count).
10. **Posture documents** (this ADR and each repository's `AGENTS.md` dependency section) are updated in the same pull request as any posture change.

### Mechanisms per ecosystem

| Ecosystem | Pins and lockfile | 24-hour age | Scripts | Audit / integrity |
|---|---|---|---|---|
| **Rust (core, server)** | Direct dependencies with exact `=x.y.z` requirements in `[workspace.dependencies]`; `Cargo.lock` committed; `--locked` everywhere | `.cargo/config.toml`: `[registry] global-min-publish-age = "1 day"` (enforced natively from Rust 1.100; until the workspace moves to 1.100, update sessions run resolution with a toolchain that enforces it); **plus a CI script** that, for every package version added or changed in a pull request's `Cargo.lock`, checks the crates.io publish time is at least 24 hours before the commit that introduced it | Build scripts cannot be disabled in Cargo: minimize crates with `build.rs`, avoid `-sys` crates that compile C, review build scripts of new dependencies | `cargo deny check` (RustSec advisories, licenses, bans, sources limited to crates.io and pinned Git tags); evaluate `cargo vet` with imported audits in Phase 2 |
| **pnpm (web)** | `packageManager` pins pnpm; `save-exact=true`; `pnpm-lock.yaml` committed; `--frozen-lockfile` | `minimumReleaseAge: 1440` with strict mode; frozen installs re-check locked versions | `strictDepBuilds: true`, empty `allowBuilds` unless justified; `ignore-scripts=true` in `.npmrc` for any npm use | `pnpm audit`; `trustPolicy: no-downgrade`; `blockExoticSubdeps`; a lockfile-integrity script (every package resolved from the npm registry with a `sha512` integrity hash; no tarball or Git sources) in place of lockfile-lint |
| **C++ (desktop)** | Qt only; version pinned in CI and packaging; installed with aqtinstall (checksums verified) at an exact version; any future vcpkg dependency pinned with `builtin-baseline` plus `overrides` | Qt release date and any baseline commit date checked by a script to be at least 24 hours old | Not applicable | Qt security advisories tracked in the monthly session |
| **Python tools in CI** (e.g. aqtinstall, REUSE) | Exact versions with `--require-hashes` | Publish dates checked in the update session | Not applicable | `pip-audit` on the tool requirements |
| **GitHub Actions** | Every `uses:` pinned to a full commit SHA (repository setting enforced); version in a trailing comment | `pinact run --check --verify-min-age --min-age 1` | Not applicable | `zizmor` on every workflow change; minimal `permissions:`; no `pull_request_target` with untrusted checkout |
| **Toolchains** (Rust, Node.js, pnpm, CMake, Qt) | Pinned exactly (`rust-toolchain.toml`, `.nvmrc`/`engines`, `packageManager`, CI) | Release date checked in the update session | — | — |

### Publishing (from Phase 1)

crates.io and npm **trusted publishing** from CI (no long-lived tokens), provenance and artifact attestations on every release, immutable releases enabled.

## Consequences

- New versions reach BayanDocs no sooner than a day after release, which blocks most "malicious version published and pulled within hours" attacks.
- Updates arrive in reviewable batches rather than a stream of bot pull requests.
- Some scripting (Cargo lockfile age check, pnpm lockfile integrity check, Qt date check) is ours to maintain; X-003 builds it once and shares it.

## Alternatives considered

- **Dependabot or Renovate version updates with delays:** rejected by owner policy.
- **Vendoring all dependencies:** strong control, but heavy repositories and awkward updates; reconsider only for the core if registry trust degrades.
- **cargo-vet from day one:** valuable but adds friction before the dependency set stabilizes; evaluate in Phase 2.

## Amendment 2026-10-04: tools in agent sessions

Agent sessions run in a Claude Code cloud environment whose setup script, [scripts/cloud-environment-setup.sh](../scripts/cloud-environment-setup.sh), installs the project's tools. It is part of the dependency posture and follows this policy:

- **Pins and age:** every tool, toolchain and package is pinned to an exact version that was at least 24 hours old when pinned; Ubuntu packages come from the signed archive frozen at a snapshot date (`apt-get --snapshot`).
- **Verification:** release archives are checked against SHA-256 hashes written in the script; Python tools are installed with `pip --require-hashes` from wheels, or, where no wheel fits (REUSE 6.2), from a hash-pinned source archive built with a hash-pinned build backend and no build isolation; Node.js against its SHA-256; pnpm through Corepack with a SHA-512 pin; Qt by aqtinstall against hashes from download.qt.io; Rust toolchains by rustup. If a release download is refused, the tool is built from source instead (Cargo with `--locked`, Go with its checksum database).
- **No silent upgrades:** rustup self-update is disabled, and Corepack must not resolve "latest" (`COREPACK_DEFAULT_TO_LATEST=0`). On 2026-10-04 Corepack's default resolved pnpm 12.9.1, published about eight hours earlier, which is why the pin is explicit. npm's user configuration sets `ignore-scripts=true`. Once the pinned Rust toolchain is 1.100 or later, the script also sets Cargo's `global-min-publish-age` globally (earlier versions only warn about it).
- **Updates:** only in the monthly dependency session, together with the repositories' own pins; Python hash lists are regenerated with [scripts/python-tool-hashes.py](../scripts/python-tool-hashes.py). The owner then pastes the new script into the environment settings ([plan/06](../plan/06-agent-workflow.md#cloud-environment-for-agent-sessions)).

## Amendment 2026-10-04: installing Qt for bayan-desktop

Decided by the owner on 2026-10-04 during DESK-001 (BayanDocs/bayan-desktop pull request 1), choosing option A below.

**Context.** aqtinstall 3.3.0 (published 2025-06-02), its newest release, cannot install Qt 6.11 or later on Windows: Qt's repository now has a separate sub-repository for each Windows compiler, which only aqtinstall's development branch supports. Qt's official online installer is no alternative, because it needs a Qt account login that CI would have to store as a secret.

**Options considered.** (A) Write a small Qt installer of our own that uses only the Python standard library, makes the same hash checks against download.qt.io as aqtinstall, and removes aqtinstall's 25 third-party Python packages from CI and developer machines; it needs this amendment. (B) Pin aqtinstall to an exact, hash-checked commit of its development branch that contains the fix: the smallest change, but it runs code that was never released. (C) Wait for aqtinstall's next release, leaving the Windows build unverified for an unknown time. The owner chose A.

**Decision.** bayan-desktop installs Qt with its own installer, `scripts/install-qt.py`, which uses only the Python standard library. In the mechanisms table above, "installed with aqtinstall" in the C++ (desktop) row now reads "installed with bayan-desktop's `scripts/install-qt.py`"; the rest of that row is unchanged.

- **Pins:** `deps/qt.json` records the exact Qt version, its release date and, for each platform, the repository path, the package and the archives to install. The 24-hour rule and the release-date check that X-003 adds apply as before.
- **Verification, with the same trust model as aqtinstall:** the repository index and every archive are checked over HTTPS against the SHA-256 hashes that Qt publishes on download.qt.io; archives are downloaded from Qt's master server (master.qt.io), never from third-party mirrors, and nothing is extracted unless its hash matches. HTTP redirects are refused, so every file comes from the server named in its URL.
- **Extraction:** every archive entry is checked before anything is extracted: no absolute paths, no "..", only plain files, directories and symbolic links that stay inside the installation, and no paths through links. Paths are compared the way case-insensitive file systems compare them (case folding and Unicode normalization), so a different spelling cannot slip past the checks on macOS or Windows, and two entries whose names differ only in case are refused unless both are directories. Links are carried from one archive to the next, so an entry of a later archive cannot pass through a link created by an earlier one, and the directory an archive is extracted into must not be, or pass through, a link. The real path of every link is checked again after each archive, and the installation is moved into place only when it is complete. Archives are extracted with the pinned CMake (`cmake -E tar`).
- **Tests:** the installer has its own tests, which run against a fake repository on disk and served over HTTP on the local machine, as part of bayan-desktop's verification gate.
- **Agent environment:** `scripts/cloud-environment-setup.sh` keeps installing its Linux Qt with aqtinstall (which supports Linux) until a monthly dependency session decides whether to switch it to this installer. When bayan-desktop is attached to a session, the setup script also runs that repository's `scripts/dev-setup.sh`, which installs its hash-pinned CMake, Ninja, clang-format and clang-tidy and reuses the preinstalled Qt. These tools are not put on the default `PATH`: the pinned CMake is version 4, which refuses projects that declare `cmake_minimum_required` below 3.5, as some older C and C++ projects still do (for example ones that Rust build scripts compile), so it must not replace the `cmake` that other repositories use. Agents working on bayan-desktop load `~/.local/share/bayandocs/desktop-tools/env.sh` first, as its `AGENTS.md` says.

**Consequences.** CI and developer machines no longer need aqtinstall's 25 third-party Python packages (some compiled, some LGPL-licensed) to install Qt. In exchange, the project maintains about 400 lines of Python (comments included) and must adapt them when Qt changes its repository layout again; the installer fails with a clear message, and installs nothing, when the index does not match the pins. `deps/qt.json` gains fields that change with every Qt version, so updating Qt in the monthly session means updating all of them and running bayan-desktop's verification gate.

## Amendment 2026-10-04: pnpm without Corepack

Node.js 25 and later no longer ship Corepack (the Node.js 26.10.0 download contains only `node`, `npm` and `npx`), and Node.js 26 is expected to become the Active LTS release in late October 2026, so the agent environment's Corepack step would break at the next Node.js update. Corepack was also weaker than it looked: it checked only pnpm's small JavaScript wrapper against the `packageManager` hash, while the 60 MB native binary that does the work was downloaded on first use and checked only against the npm registry's signature. Corepack is therefore no longer used anywhere:

- **Agent environment:** [scripts/cloud-environment-setup.sh](../scripts/cloud-environment-setup.sh) installs pnpm's native binary, the npm package `@pnpm/exe.linux-x64` at the pinned `PNPM_VERSION`, only after checking it against a SHA-512 hash written in the script (in hex, like the other pins), and puts it on `PATH` ahead of Node.js. The `COREPACK_*` settings are gone.
- **Inside each repository**, pnpm switches itself to the version pinned in that repository's `packageManager` field, verified against the repository's lockfile and npm's signature.
- **bayan-web** pins pnpm's native binary through its lockfile: the first YAML document of `pnpm-lock.yaml` records the sha512 of `@pnpm/exe.<platform>` for each supported platform, and its `scripts/dev-setup.sh` installs that binary only after checking the download against it. Its policy check also fails when the pnpm running the gate (reported in `npm_config_user_agent`) is not the pinned version.
- **Updates:** the pnpm pin in the setup script changes only in the monthly dependency session, like every other pin.

This amendment replaces the Corepack parts of the amendment "tools in agent sessions" above ("pnpm through Corepack with a SHA-512 pin" and `COREPACK_DEFAULT_TO_LATEST=0`); the rest of that amendment, and the amendment on installing Qt for bayan-desktop, still apply.

## Revisit when

Ecosystem tools change (for example Cargo re-checking lockfile ages natively, or lockfile-lint supporting pnpm), a supply-chain incident affects us, or the owner changes the policy.
