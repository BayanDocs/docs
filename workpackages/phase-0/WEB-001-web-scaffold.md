# WEB-001: Web scaffold and CI

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | WEB |
| Repository | bayan-web |
| Attach to session | bayan-web, docs |
| Size | M |
| Depends on | — |
| Unblocks | WEB-002, X-003 |
| Status | Ready |
| Requirements | ARC-03, SEC-10, PERF-06, PLT-02 |
| Decisions | ADR-0014 (implement it), ADR-0017, ADR-0012 |
| Specs | — |

## Context

The web shell is a thin React and TypeScript application that will run the engine in a Web Worker. ADR-0014 fixes the stack (React, TypeScript strict, Vite, React Aria Components, Biome, Vitest, Playwright, pnpm) and the security headers; ADR-0017 fixes the dependency rules, several of which pnpm enforces natively.

## Objective

A secure, minimal, fully gated React application skeleton with pnpm configured to enforce the dependency policy and tests running in three browser engines.

## Scope

### In scope

- pnpm pinned via `packageManager` (the newest major's release at least 24 hours old), with `minimumReleaseAge: 1440` and strict mode, `strictDepBuilds: true`, an empty `allowBuilds` list, `trustPolicy: no-downgrade`, exotic sub-dependencies blocked, `save-exact`, and `.npmrc` with `ignore-scripts=true`. Node.js pinned to the current Active LTS release.
- Vite, React and TypeScript (strict) app skeleton: application frame with a placeholder ribbon region and a canvas region; light and dark themes; React Aria Components installed and used for at least one control to establish the pattern.
- Biome for linting and formatting; `tsc --noEmit`; Vitest unit tests; Playwright end-to-end smoke test in Chromium, Firefox and WebKit.
- Security headers in the dev and preview servers and in a sample production configuration: strict Content Security Policy (`script-src 'self' 'wasm-unsafe-eval'`, no inline scripts), Trusted Types, cross-origin isolation (`Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Embedder-Policy: require-corp`), `Integrity-Policy` for scripts, and Subresource Integrity attributes on built scripts (via a small, dependency-free post-build step if the build tool cannot do it).
- `pnpm verify` running install checks, lint, type check, unit tests, end-to-end tests and `pnpm audit`.
- CI workflow running `pnpm install --frozen-lockfile` and `pnpm verify`, following ADR-0017 workflow conventions.
- Update this repository's `AGENTS.md` and `README.md` with real commands.

### Out of scope

The engine worker, canvas and input bridge (WEB-002); the lockfile integrity script (X-003).

## Deliverables

Project, configuration, tests, CI workflow, documentation updates.

## Acceptance criteria

- [ ] AC-1 CI is green; Playwright smoke passes in all three engines.
- [ ] AC-2 A test verifies every security header on the preview server, and the built page loads with no CSP violations.
- [ ] AC-3 No dependency install or build scripts run (pnpm output shows none allowed); attempting to add a package with an install script fails the install.
- [ ] AC-4 Every dependency is exact-pinned, at least 24 hours old (pnpm enforces), allowlisted and justified in the pull request, with the total package count reported.
- [ ] AC-5 Production bundle size is reported and below 300 KB compressed for the skeleton.

## Verification

`pnpm verify`; CI links.

## Notes and pitfalls

Playwright's browser downloads are tied to its version; pin it like any other dependency.

## Escalate if

A required tool cannot work with install scripts disabled.
