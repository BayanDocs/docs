# Architecture Decision Records

An Architecture Decision Record (ADR) captures one significant decision: the context, what was decided, the consequences, the alternatives rejected, and what would make us revisit it. Accepted ADRs are binding on all work. The process is defined in [ADR-0001](0001-record-architecture-decisions.md); new ADRs start from [0000-template.md](0000-template.md).

Facts about third-party projects (versions, licenses, feature support) were verified on 2026-10-03 against primary sources (package registries, project documentation, standards bodies). Work packages re-verify them when they pin versions.

## Status legend

| Status | Meaning |
|---|---|
| Accepted | Binding. |
| Accepted — validation gate | Binding, but a named spike or work package must confirm specific criteria; if they fail, the ADR is amended at the next gate review. |
| Proposed | Not yet binding. Awaiting owner confirmation or evidence. |
| Superseded by ADR-NNNN | Kept for history. |

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-repository-topology-and-contracts.md) | Repository topology, versioning and cross-repository contracts | Accepted |
| [0003](0003-licensing-and-contribution-model.md) | Licensing and contribution model | Accepted (owner, 2026-10-04); in force since 2026-10-04 |
| [0004](0004-fidelity-contract-and-determinism.md) | Fidelity contract and layout determinism | Accepted |
| [0005](0005-layout-units-and-deterministic-math.md) | Integer layout units (BLU) and deterministic math | Accepted |
| [0006](0006-rust-core-and-memory-safety.md) | Rust core and memory-safety policy for untrusted input | Accepted |
| [0007](0007-document-model.md) | Document model: a Word-shaped stream of stories and atoms | Accepted — validation gate (CORE-004) |
| [0008](0008-crdt-engine-and-local-first.md) | CRDT engine (Loro) and local-first architecture | Accepted — validation gate (CORE-004) |
| [0009](0009-text-stack.md) | Text stack: shaping, Unicode, line breaking and the Word measurement model | Accepted — validation gate (CORE-003) |
| [0010](0010-font-strategy.md) | Font strategy and the bundled font library | Accepted |
| [0011](0011-rendering-pipeline.md) | Rendering pipeline: display lists, reference rasterizer, PDF | Accepted — validation gate (CORE-003) |
| [0012](0012-engine-boundary.md) | Engine boundary: JSON message protocol, C ABI and WebAssembly | Accepted |
| [0013](0013-desktop-shell.md) | Desktop shell: Qt 6 Quick with thin C++ | Accepted — validation gate (DESK-002) |
| [0014](0014-web-shell.md) | Web shell: React and TypeScript, engine in a Web Worker | Accepted — validation gate (WEB-002) |
| [0015](0015-server-architecture.md) | Server: single Rust binary, zero-knowledge relay | Accepted |
| [0016](0016-e2ee-and-identity.md) | End-to-end encryption and identity with MLS | Accepted — validation gate (SRV-002, external review before GA) |
| [0017](0017-supply-chain-and-dependency-policy.md) | Supply-chain and dependency policy | Accepted; amended 2026-10-04 (agent environment; installing Qt for bayan-desktop; what the license allowlist covers; pnpm without Corepack) |
| [0018](0018-file-formats-and-priorities.md) | File formats and conversion priorities | Accepted |
| [0019](0019-shared-ui-manifest.md) | Shared UI manifest; Classic and Focus modes | Accepted |
| [0020](0020-accessibility-release-gate.md) | Accessibility is a release gate | Accepted |
| [0021](0021-internationalization.md) | Internationalization and localization | Accepted |
| [0022](0022-proofing-tools.md) | Proofing tools: spelling, grammar, hyphenation | Accepted |
| [0023](0023-automation-macros-active-content.md) | Automation, macros and active-content security | Accepted |
| [0024](0024-local-ai.md) | Local AI | Accepted |
| [0025](0025-quality-gates.md) | Quality gates: determinism, fidelity, fuzzing, performance | Accepted |
| [0026](0026-release-engineering.md) | Release engineering, signing and updates | Accepted |
| [0027](0027-documentation-tooling.md) | Documentation tooling | Accepted |
