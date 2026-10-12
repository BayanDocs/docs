# ADR-0014: Web shell — React and TypeScript, engine in a Web Worker

- **Status:** Accepted — validation gate (WEB-002), results proposed on 2026-10-12 (see the amendment of that date): met in part, with manual screen-reader, input-method and Safari passes outstanding
- **Date:** 2026-10-03
- **Deciders:** Planner (the owner left the framework open among React, Vue and Svelte)
- **Related:** ARC-03, ARC-05, SEC-10, A11Y-02, PERF-06, PLT-02, ADR-0012, ADR-0017, ADR-0019, WEB-001, WEB-002

## Context

The web application must render engine pages pixel-identically to desktop, stay responsive while the engine works, support input methods and screen readers despite drawing the document on a canvas, work offline, and be hardened against script injection because it handles end-to-end-encrypted content. Browser support facts verified on 2026-10-03 (current: Chrome 154, Firefox 157, Safari 27):

| Capability | Chromium | Firefox | Safari |
|---|---|---|---|
| EditContext (input for custom editors) | yes (121+) | no (positive position) | no |
| OffscreenCanvas 2D in workers | yes | yes (105+) | yes (16.4+) |
| WebAssembly SIMD128 / threads | yes / yes | yes / yes | yes (16.4+) / yes (no COEP `credentialless`) |
| WebAssembly 64-bit memory | yes (133+) | yes (134+) | **no** |
| JS Promise Integration (JSPI) | yes (137+) | yes (153+) | yes (27+) |
| Origin Private File System | yes | yes | yes |
| File System Access pickers | yes | no | no |
| `Integrity-Policy` header (enforced SRI) | yes (138+) | yes (145+) | yes (26+) |

## Decision

1. **React with TypeScript (strict mode) and Vite**, with **React Aria Components** as the foundation for accessible interface controls. Interfaces are generated from the shared UI manifest (ADR-0019).
2. **pnpm** as the package manager, pinned through `packageManager`, configured per ADR-0017: `minimumReleaseAge: 1440` with strict mode, dependency build scripts blocked (`strictDepBuilds`, empty `allowBuilds` allowlist unless justified), `trustPolicy: no-downgrade`, exotic sub-dependencies blocked, exact versions saved, frozen-lockfile installs in CI.
3. **Biome** for linting and formatting (a single binary, far fewer dependencies than ESLint plus Prettier plugin trees); `tsc --noEmit` for type checking; **Vitest** and **Playwright** for tests; **axe** rules for automated accessibility checks.
4. **Engine in a dedicated module Web Worker.** The main thread runs React, the input bridge and a **tile compositor** that draws engine-produced `ImageBitmap` tiles onto the visible canvas and draws overlays, so scrolling stays smooth while the engine is busy.
5. **Input bridge:** EditContext where available; elsewhere a hidden, caret-positioned editable element that captures composition, `beforeinput` and clipboard events. Both implement one `InputBridge` interface.
6. **Accessibility mirror:** an off-screen DOM built from the engine's accessibility tree (headings, paragraphs, lists, tables, links, images with alternative text), kept in sync with the caret and selection, so screen readers can read and navigate the document.
7. **Storage:** Origin Private File System for working state and the recovery journal; File System Access pickers where available, download/upload elsewhere.
8. **Single-threaded WebAssembly (wasm32) first.** Threads are an optimization for Phase 2, enabled only on deployments that serve cross-origin isolation headers. 64-bit memory is not used until Safari supports it; memory budgets assume a 4 GB ceiling. The async message design does not require JSPI.
9. **Security hardening:** a strict Content Security Policy (`script-src 'self' 'wasm-unsafe-eval'`, no inline scripts), Trusted Types, `Integrity-Policy` with Subresource Integrity on every script, cross-origin isolation headers, no third-party origins at runtime, no analytics.
10. **Installable PWA** with a hand-written service worker for offline use.

## Consequences

- React's ecosystem and its familiarity to agents speed up development; React Aria handles the hardest accessibility patterns (menus, comboboxes, dialogs, grids).
- The canvas architecture requires us to build the input bridge and accessibility mirror ourselves; WEB-002 de-risks both early.
- Without threads, very large documents lay out more slowly in the browser than on desktop; PERF budgets for the web account for that.

## Alternatives considered

- **Svelte 5, Vue, Solid:** smaller bundles, but smaller accessible-component ecosystems and less agent familiarity.
- **Rendering the document as DOM (contenteditable):** gives input and accessibility for free but cannot guarantee identical layout to desktop. Rejected by ADR-0004.
- **Engine on the main thread:** simpler, but long layouts would freeze the interface.
- **npm or Yarn:** both now offer release-age gates, but pnpm re-checks the age of locked versions on frozen installs and has the strictest script controls.

## Validation gate

WEB-002 must show smooth scroll and zoom of worker-rendered tiles in Chromium, Firefox and WebKit; IME composition (Japanese, Chinese, Korean) reaching the engine through both bridge implementations; a screen reader (NVDA with Firefox or Chrome, VoiceOver with Safari) reading text from the accessibility mirror; and keystroke-to-overlay latency measurements.

## Revisit when

EditContext ships in Firefox and Safari (simplify the bridge); Safari ships 64-bit memory (raise memory budgets); WEB-002 fails its criteria.

## Amendment 2026-10-12: results of the WEB-002 validation gate

Proposed on 2026-10-12 by WEB-002 ([BayanDocs/bayan-web pull request 7](https://github.com/BayanDocs/bayan-web/pull/7)), for the owner to decide. The spike's full report, with every figure, test and transcript, is [`docs/spikes/WEB-002-report.md`](https://github.com/BayanDocs/bayan-web/blob/d3e8ac79f57b6d526dcaadc46d07eecd8e6e06bd/docs/spikes/WEB-002-report.md) in bayan-web. The spike ran CORE-007's engine skeleton and mock document, built from a pinned bayan-core commit (ADR-0002), in Playwright 1.63's Chromium 153, Firefox 155 and WebKit 26.6, headless, in a Linux cloud container with four virtual cores and no graphics processor; CI repeated the measurements on GitHub's macOS 15 (Apple Silicon) and macOS 26 (Intel) virtual machines.

**Validation result: met in part, with no criterion failed.** Decisions 4, 5, 6 and 9 stand as written, made precise below. What remains are passes that need real hardware or a person, listed at the end of this amendment.

1. *Smooth scroll and zoom of worker-rendered tiles.* Met in Chromium and Firefox on Linux: scrolling at 1,500 CSS pixels a second and eight zoom steps ran at 60 frames a second (p95 frame interval 16.7 and 17.3 ms), with no frame over 33 ms and no blank page; Firefox did the same on CI's Apple Silicon Mac. In WebKit, met at a device-pixel ratio of 1 on Linux (p50 18.3 ms, p95 23.5 ms, 2 of 199 frames over 33 ms) and at a ratio of 2 on CI's Apple Silicon Mac in two runs (p95 19.2–19.5 ms scrolling, 18.0–19.6 ms zooming, no blank page); not at a ratio of 2 on Linux, about 16 frames a second, because Playwright's WebKit there draws in software, and 12–13 frames per run there showed a blank area while scrolling. Two CI results are not yet explained and point at the virtual machines rather than the code: Playwright's Chromium on the Apple Silicon Mac was irregular (30 frames a second in one run; in the other, 60 at the median but 22 of 120 scroll frames over 33 ms and one with a blank area), and the Intel Mac was slow in every browser, with WebKit showing a blank area in 21 and 10 frames while scrolling. While zooming, every browser showed the previous scale's tiles scaled until fresh ones arrived, and no frame in any run showed a blank page. Real Safari and Chrome on Macs are part of the manual pass.
2. *IME composition (Japanese, Chinese, Korean) through both bridge implementations.* Met with automated evidence. In Chromium, the DevTools protocol's input-method emulation composed all three languages through the EditContext bridge and, with EditContext removed, through the hidden-text-area bridge; the engine received every composition step and the committed text, and drew both. In Firefox and WebKit, Playwright cannot drive an input method, so the tests replay in those engines the events a browser fires while an input method composes, with the same result. Real input methods in Firefox and Safari, whose event order differs in known ways, are part of the manual pass.
3. *A screen reader reading text from the accessibility mirror.* Met with Orca 46.1, the Linux screen reader, in Firefox 155 and Chromium 141, not yet with the NVDA or VoiceOver this gate names: Orca read the mirror's headings, paragraphs, list and table, and followed the engine's caret while typing through both bridges (transcripts in the report's evidence folder). Three problems found that way were fixed: focus moves to the editable text on pointer release rather than press (otherwise Orca stays in browse mode and takes typing as commands), the mirror's table carries an explicit `role="table"` (otherwise Firefox takes it for a layout table), and browser spell checking is off on both bridges. Passes with NVDA and with VoiceOver are scripted in the report for the owner.
4. *Keystroke-to-overlay latency measurements.* Met: measured, as lower bounds, with a plan. With steady typing (12 characters a second), the frame in which the browser will paint the new caret starts 3.6–18.3 ms after the key at p95 in Chromium, Firefox and WebKit at a ratio of 1 on Linux, and the typed character is drawn into the canvas within 22–38 ms; Firefox and WebKit at a ratio of 2 on CI's Apple Silicon Mac gave similar figures (caret frame 19.4–21.3 ms at p95). These figures stop before the browser paints, composites and presents the frame and before the display shows it, which headless browsers do not measure, so they are lower bounds of PERF-04's keystroke-to-pixel latency (at most 16 ms at p95 and 33 ms at p99, first due in Phase 2, Writer): they show PERF-04 missed at p95, by 1–3 ms for the caret in some runs and clearly for the character, and cannot show it met at p99. The engine's own share is small; the rest is waiting for the next frame and, in bursts, for the worker. The report's plan: measure keystroke-to-pixel itself on real 60 Hz and 120 Hz screens, the display included (the browsers' performance recorders for key to frame presented, a slow-motion camera for key to pixel), coalesce typed text while an answer is pending and keep tile work behind input, render only invalidated lines (the shell already asks for partial tiles), try a desynchronized overlay canvas, and in Phase 2 move rasterization off the engine's message queue (Decision 8). WEB-101 re-measures with the real engine.

**Design details settled by the spike.**

1. *Trusted Types (Decision 9).* The Content Security Policy is WEB-001's with one change: `trusted-types bayan-script-url`. That one policy is created in one module of the app (a test fails if `createPolicy` appears anywhere else), implements only `createScriptURL`, and accepts nothing but the exact same-origin paths of the app's own built worker scripts, which the build writes into it; it refuses every other address. It is the only way any script URL reaches a worker, and the PWA's service worker (Decision 10) will use the same policy. Any further policy needs an amendment of this ADR.
2. *Integrity of the engine's files (Decision 9).* Browsers check no integrity for a worker's script, the modules it imports or the WebAssembly it fetches: `new Worker()` takes no integrity option, and `Integrity-Policy` covers only the `script` and `style` destinations (verified in Chromium, Firefox and WebKit with the production headers). The app therefore checks the engine itself: the build serves the engine's three runtime files unchanged from a content-addressed folder and writes their SHA-384 hashes into the app's own bundle, which `index.html` loads with Subresource Integrity; before starting the worker, the app fetches all three with those hashes and starts nothing if any differs or is missing. The build's integrity check exempts exactly those engine scripts, and only when they are byte-identical to the engine package, and still fails for every other script without a hash. A gap remains: the browser does not bind the worker's own requests to the bytes the app checked, so an origin or intermediary that serves different bytes to the two requests is not detected (a file tampered with at rest is). Closing it needs the worker host to accept the module's hash (a small bayan-core change) and, for the scripts, either the PWA's service worker checking responses against a manifest of hashes or a browser feature that does not exist yet.
3. *Tile compositor (Decision 4).* Canvas 2D on the main thread, tiles of 512 device pixels on each page's own pixel grid, one tile request in flight, the previous scale's tiles drawn scaled until fresh ones arrive, partial tiles (patches) for small invalidations such as a typed character, and the caret drawn as soon as the engine answers rather than in the next frame. If Safari on real hardware stays below 60 frames a second at a ratio of 2, the compositor lets the browser scroll the tiles itself (tile canvases inside the scrolled content); that changes the shell, not the protocol.
4. *Input bridge (Decision 5).* EditContext where available (Chromium), the hidden text area elsewhere, both behind one interface. Until the engine protocol can replace and delete ranges, the bridges switch off the browser's own suggestions and spell checking and forward deletions by word or line as keys.
5. *Accessibility mirror (Decision 6).* The editable text in the mirror is the input bridge's own element, holding the engine's text and caret, so that screen readers follow the engine's caret there; lists and tables carry explicit roles, because the mirror is invisible and browsers otherwise discount them.

**Outstanding before the gate counts as fully met.** Manual passes by the owner, recorded in the report: real Japanese, Chinese and Korean input methods in Firefox and Safari; NVDA with Firefox or Chrome and VoiceOver with Safari; frame times in Safari and Chrome on real Macs, and keystroke-to-pixel latency, the display included, on real 60 Hz and 120 Hz screens. The spike's other follow-ups (protocol additions for ranges, clipboard bytes, narrower invalidation and the platform's primary shortcut modifier; the worker host's module hash; automated accessibility rules) are listed in the report and belong to later work packages.

**Revisit when** (in addition to the list above): a browser ships integrity for worker scripts, which closes the gap in detail 2; or Safari stays below 60 frames a second on real hardware after the change in detail 3.
