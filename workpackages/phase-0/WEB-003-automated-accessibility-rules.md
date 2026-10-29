# WEB-003: Automated accessibility rules (axe) in the web app's end-to-end tests

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | WEB / A11Y-I18N |
| Repository | bayan-web |
| Attach to session | bayan-web, docs |
| Size | S |
| Depends on | WEB-002 |
| Unblocks | WEB-102 (accessibility work builds on a checked baseline) |
| Status | Ready |
| Requirements | A11Y-01 |
| Decisions | ADR-0014 (decision 3, and its amendment of 2026-10-12), ADR-0017, ADR-0020 (decision 6) |
| Specs | — |

## Context

[ADR-0020](../../adr/0020-accessibility-release-gate.md) decision 6 says that "automated accessibility checks run on every pull request", and [ADR-0014](../../adr/0014-web-shell.md) decision 3 names axe rules for the web app. *axe* (axe-core) is a library of automated accessibility rules: it inspects a page's structure, names, roles and states against the Web Content Accessibility Guidelines (WCAG) and lists what it finds. The architecture review of 2026-10-27, finding [M9](../../plan/reviews/2026-10-27.md#m9-no-automated-accessibility-checks-and-the-manual-validation-passes-are-still-open), found that bayan-web has no rule-based checks; the WEB-002 report already listed them as its follow-up F9 ([WEB-002-report.md:339](https://github.com/BayanDocs/bayan-web/blob/01c59788fa755eea8665332d88b18174a90e1a22/docs/spikes/WEB-002-report.md#L339)). This still holds at `01c5978`: nothing in the repository uses axe.

What exists: Playwright 1.63.0 runs the end-to-end tests in `tests/e2e/` in Chromium, Firefox and WebKit against the production build, served with the production security headers ([playwright.config.ts](https://github.com/BayanDocs/bayan-web/blob/01c59788fa755eea8665332d88b18174a90e1a22/playwright.config.ts)). `a11y.spec.ts` tests the accessibility mirror (the hidden copy of the document's structure that assistive technology reads, while the canvas's pixels are hidden from it). [`collect-problems.ts`](https://github.com/BayanDocs/bayan-web/blob/01c59788fa755eea8665332d88b18174a90e1a22/tests/e2e/collect-problems.ts) makes a test fail on any Content Security Policy or Trusted Types violation, console error or uncaught exception. The policy requires Trusted Types for scripts and allows exactly one policy, `bayan-script-url` ([config/security-headers.ts:27](https://github.com/BayanDocs/bayan-web/blob/01c59788fa755eea8665332d88b18174a90e1a22/config/security-headers.ts#L27)); ADR-0014's amendment of 2026-10-12 says that "any further policy needs an amendment of this ADR".

The manual validation passes of M9 (NVDA, VoiceOver, input methods on Windows and macOS and in Firefox and Safari, frame times on real Macs) stay with the owner and are not part of this work package.

## Objective

Every pull request runs axe's WCAG rules on the web app's pages in all three browsers, and fails on any violation.

## Scope

### In scope

- **The dependency.** `@axe-core/playwright` as an exact-pinned development dependency, which brings `axe-core`; both are MPL-2.0, which ADR-0017's allowlist includes. Each version at least 24 hours old, with no install script (pnpm's `strictDepBuilds` stays as it is), and justified in the pull request as AGENTS.md §5 requires: what it does, why the project cannot reasonably write it, the alternatives (pa11y and Lighthouse, which bring a browser automation stack of their own; Playwright's ARIA snapshots, which compare structure but check no rules), the license, its maintenance, the publish date of each version and the number of packages it adds.
- **The checks.** A spec in `tests/e2e/` that runs axe with the tags of WCAG 2.0, 2.1 and 2.2 at levels A and AA (A11Y-01 asks for WCAG 2.2 AA) on every state the app has today: the page as it loads, the document open with its mirror built, and every dialog, menu or other state that the existing end-to-end tests reach. It runs in Chromium, Firefox and WebKit and fails on any violation, listing the rule, the element and axe's help text. No rule is disabled, and none excluded for an element, unless the spec says why next to the setting and the pull request explains it.
- **The security headers stay as they are.** axe runs under the production Content Security Policy and Trusted Types, with no `bypassCSP`, no new Trusted Types policy and no change to the headers, and `collectProblems` still reports nothing in these tests.
- **Fixes.** Violations that axe finds in the current app are fixed in this pull request when the fix is small and inside the shell; anything larger is a follow-up (see "Escalate if").
- **Documentation.** bayan-web's `AGENTS.md` (the `test:e2e` description and the dependency mechanisms) and `README.md` if it lists the tests.

### Out of scope

- The owner's manual passes with screen readers and input methods.
- Rules for bayan-desktop's Qt interface, for which no comparable tool exists; record it as a follow-up if useful.
- Accessibility of document content, which the accessibility checker of A11Y-04 covers later.

## Deliverables

- The pinned development dependencies in `package.json` and `pnpm-lock.yaml`.
- The new spec, any shared helper, and the fixes.
- The documentation above.

## Acceptance criteria

- [ ] AC-1 The pull request justifies the new packages as AGENTS.md §5 requires, with the publish date of each version at least 24 hours before it was added.
- [ ] AC-2 The spec runs axe with the WCAG 2.0, 2.1 and 2.2 A and AA tags on every listed state in Chromium, Firefox and WebKit, and passes with no violations and no problems reported by `collectProblems` (CI links for the three runners of `pnpm verify`).
- [ ] AC-3 A deliberate violation (for example a button without an accessible name, added for the experiment and then removed) makes the spec fail in each browser with the rule's name (output).
- [ ] AC-4 The production headers are unchanged (the security tests and the headers' unit test pass unchanged), and no test uses `bypassCSP`.
- [ ] AC-5 `pnpm verify` passes, including `check:policy`, `check:lockfile` and `audit`.

## Verification

`pnpm verify`; `pnpm exec playwright test tests/e2e/<the new spec>` in each browser; the experiment of AC-3; the CI runs on `ubuntu-24.04`, `macos-15` and `macos-26-intel`.

## Notes and pitfalls

- `@axe-core/playwright` injects axe's code into the page through Playwright, which the page's Content Security Policy does not block, but axe's own code then runs inside the page under Trusted Types; if any of its checks writes to a sink that Trusted Types guards, the browser reports a violation and `collectProblems` fails the test. Find out early, in all three browsers.
- The mirror is built from the engine's accessibility tree and changes as the document does; wait for it the way `a11y.spec.ts` does before running axe.
- The canvas is hidden from assistive technology on purpose (`aria-hidden`); axe does not read pixels, so it checks the mirror and the shell's controls.
- Keep the Playwright version as it is; the browser builds in `scripts/dev-setup.sh` are pinned to it.

## Escalate if

- axe cannot run under the production Content Security Policy and Trusted Types without a new policy or a change to the headers, which would need an amendment of ADR-0014.
- axe reports a violation whose fix belongs to the engine (for example in the accessibility tree it sends, whose gaps finding H5 assigns to the protocol) or to a design decision; propose disabling that rule with a recorded reason and a follow-up, rather than leaving the spec red.
