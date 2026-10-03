# ADR-0023: Automation, macros and active-content security

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** AUT-01…AUT-06, SEC-02, SEC-03, [plan/07 — document-borne threats](../plan/07-quality-security-testing.md#document-borne-threats-we-refuse-to-replicate), ADR-0006

## Context

The specification asks for a sandboxed layer that runs legacy VBA macros or instantly translates them to modern JavaScript or Python. VBA is a full language bound to Word's very large object model; LibreOffice has worked on partial VBA compatibility for many years. Macros and other active content (DDE fields, remote templates, OLE, external links) are also the most abused attack vectors in Word's history. Facts verified on 2026-10-03: **Boa** (`boa_engine` 0.22, MIT/Unlicense) is a pure-Rust JavaScript engine passing about 95.6% of the ECMAScript conformance suite and building for WebAssembly; **rquickjs** binds the C engine QuickJS-NG.

## Decision

### Stages

| Stage | What | Phase |
|---|---|---|
| 1. Preserve | VBA projects, signatures and active content are preserved untouched in `.docm`/`.dotm` and never executed | P1 |
| 2. Inspect | Read-only viewer of VBA source (decompressed per MS-OVBA) with a security summary | P4 |
| 3. Automate | A modern **Bayan Automation API** for JavaScript/TypeScript, executed in a sandbox | P5 |
| 4. Translate | Assisted VBA → JavaScript translation (rule-based for common patterns, local AI for the rest) with a side-by-side review interface; translation coverage is measured and published | P5 |
| 5. Compatibility | An opt-in, sandboxed runtime for a documented subset of the Word object model, so common legacy macros can run with user consent | P6 |

### Rules

1. **Nothing runs automatically.** Auto-run macros, document-open events and DDE never execute. Running anything requires an explicit, per-document user action, and administrators can disable automation entirely.
2. **Sandbox:** scripts run in **Boa**, a pure-Rust engine, inside the engine's process with no ambient authority: no file system, network, clipboard, or other documents unless the user grants a capability at a prompt. Execution time, memory and recursion are limited. C-based engines may be used only inside a WebAssembly sandbox.
3. **Extensions** (Phase 5) are WebAssembly components with declared capabilities, running in wasmtime on desktop and in the browser on the web, so one extension works identically on both.
4. **Active-content blocking** follows the table in [plan/07](../plan/07-quality-security-testing.md#document-borne-threats-we-refuse-to-replicate): external relationships, remote templates, INCLUDE fields, OLE activation, dangerous URL schemes and UNC paths are never resolved automatically.
5. **Python** automation is not planned; it may be offered later as an extension if demand appears.

## Consequences

- BayanDocs is safe to open untrusted documents in by default, a real advantage over Word's history.
- Users depending on complex macros will not get full compatibility early; expectations are set clearly in documentation and in the product.

## Alternatives considered

- **Embedding a full VBA interpreter early:** enormous effort and attack surface for limited early value.
- **Promising instant, complete VBA translation:** not achievable; rejected in favor of measured coverage.
- **QuickJS (C) as the main engine:** faster and very compatible, but contrary to ADR-0006 outside a WebAssembly sandbox.

## Revisit when

User research shows a large share of target users blocked by macros; Boa's performance or conformance proves insufficient.
