# ADR-0014: Web shell — React and TypeScript, engine in a Web Worker

- **Status:** Accepted — validation gate (WEB-002)
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
