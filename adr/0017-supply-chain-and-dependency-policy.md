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
8. **License allowlist:** MIT, MIT-0, Apache-2.0 (including the LLVM exception), BSD-2-Clause, BSD-3-Clause, ISC, Zlib, 0BSD, BSL-1.0, CC0-1.0, Unicode-3.0, Unicode-DFS-2016, MPL-2.0. Fonts and data packs may also use OFL-1.1, the GUST Font License, CC BY 4.0 and LGPL with font exceptions. Qt is used under LGPL-3.0 (dynamic linking). Anything else requires an ADR amendment. Dual-licensed packages qualify if one option is on the list.
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

## Revisit when

Ecosystem tools change (for example Cargo re-checking lockfile ages natively, or lockfile-lint supporting pnpm), a supply-chain incident affects us, or the owner changes the policy.
