# X-003: Supply-chain enforcement and the monthly update runbook

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | SECURITY |
| Repository | bayan-core, bayan-server, bayan-web, bayan-desktop (+ docs for the runbook) |
| Attach to session | all five repositories |
| Size | M |
| Depends on | CORE-001, SRV-001, WEB-001, DESK-001 |
| Unblocks | Every later dependency change; monthly update sessions |
| Status | Ready |
| Requirements | SEC-05 |
| Decisions | ADR-0017 (implement it exactly), ADR-0006 |
| Specs | — |

## Context

ADR-0017 encodes the owner's dependency policy and lists, per ecosystem, the mechanisms that enforce it. Some are native settings (pnpm's release-age gate, Cargo's `global-min-publish-age` from Rust 1.100), and some must be scripted (Cargo does not re-check versions already in `Cargo.lock`; lockfile-lint does not support pnpm; there is no release-age gate for Qt). Read ADR-0017 in full before starting.

## Objective

Every rule in ADR-0017 is enforced automatically in CI in every code repository, and a step-by-step runbook makes the monthly update session repeatable.

## Scope

### In scope

- **All code repositories:** a check that fails if `.github/dependabot.yml`/`.yaml`, `renovate.json`, `.renovaterc*`, `.github/renovate.json*` or similar update-bot configuration exists.
- **Rust (core, server):**
  - `.cargo/config.toml` with `[registry] global-min-publish-age = "1 day"`;
  - `deny.toml` implementing the license allowlist, sources (crates.io plus explicitly allowed Git repositories at pinned revisions), bans (duplicate-version warnings), and advisories;
  - an `xtask` subcommand `check-lockfile-age`: for every package version added or changed in the pull request's `Cargo.lock` (diff against the merge base), fetch its publish time from the crates.io sparse index (`pubtime`) or API (`created_at`), and fail if it is less than 24 hours before the commit that introduced it or before now; it must send a descriptive User-Agent, respect crates.io rate limits, and work offline for unchanged lockfiles;
  - an `xtask` subcommand `check-exact-pins` ensuring every entry in `[workspace.dependencies]` uses an exact `=x.y.z` requirement;
  - both wired into `cargo xtask verify` and CI.
- **pnpm (web):**
  - confirm the settings from ADR-0017 are present (`minimumReleaseAge: 1440` with strict mode, `strictDepBuilds`, empty `allowBuilds`, `trustPolicy: no-downgrade`, exotic sub-dependencies blocked, `save-exact`, `ignore-scripts=true` in `.npmrc`);
  - a dependency-free Node script `scripts/check-lockfile-integrity.mjs` that fails unless every package in `pnpm-lock.yaml` resolves from `registry.npmjs.org` with a `sha512` integrity hash and no tarball, Git or file sources;
  - `pnpm audit` gate (fail on high and critical; moderate reported).
- **Desktop:** a pin file (for example `deps/qt.json`) recording the exact Qt version, its release date and the aqtinstall version; a script that fails CI if the release date is less than 24 hours before the commit; checksum verification confirmed in the Qt install step.
- **Python tools in CI:** requirements files with exact versions and `--require-hashes`; `pip-audit` on them.
- **Runbook:** `docs/developer/dependency-update-runbook.md` (create the folder if needed) with exact steps per repository for the monthly session and the security-alert session, matching the prompts in `docs/plan/06-agent-workflow.md`, including how to handle a fix younger than 24 hours.
- Update each repository's `AGENTS.md` dependency section to describe the real mechanisms (posture document rule).

### Out of scope

- `cargo vet` (Phase 2 evaluation).
- Changing any dependency versions (that is the monthly session's job).

## Deliverables

One pull request per code repository plus one to docs for the runbook.

## Acceptance criteria

- [ ] AC-1 Each check fails on a deliberately violating fixture or test branch and passes on the clean state; evidence for every check is in the pull request.
- [ ] AC-2 `check-lockfile-age` correctly evaluates a sample diff containing a version published less than 24 hours earlier (use a recorded fixture of index data in tests so tests do not depend on the network).
- [ ] AC-3 `cargo deny check` and `pnpm audit` run in CI and pass.
- [ ] AC-4 The runbook lets a fresh agent perform a monthly update in each repository without other instructions (reviewer confirms).
- [ ] AC-5 Every `AGENTS.md` dependency section matches the implemented mechanisms.

## Verification

`cargo xtask verify` (core, server), `pnpm verify` (web), the desktop verify workflow, and CI runs showing failing and passing cases.

## Notes and pitfalls

- Until the workspace toolchain is Rust 1.100 or later, Cargo ignores `global-min-publish-age`; the lockfile-age check is what protects us meanwhile.
- The crates.io sparse index is the cheapest source of `pubtime`; cache responses within a CI run.
- 2026-10-04: bayan-desktop no longer uses aqtinstall ([ADR-0017](../../adr/0017-supply-chain-and-dependency-policy.md), amendment of 2026-10-04). Its pin file, `deps/qt.json`, records the Qt version and release date but no aqtinstall version, and the Qt install step is `scripts/install-qt.py`, whose checksum verification is covered by its own tests.

## Escalate if

A mechanism in ADR-0017 turns out not to work as described with the pinned tool versions; propose an amendment rather than weakening the rule.
