# BayanDocs Knowledge Base

BayanDocs is a free, open-source word processor built to match or exceed Microsoft Word in document fidelity, features and speed, while adding what Word cannot offer: layout that is identical on every platform, local-first editing, and zero-knowledge end-to-end-encrypted collaboration that anyone can self-host.

This repository is the project's single source of truth. Today it holds the master plan, the architecture decision records, the technical specifications and the work packages that agents execute. Over time it will also hold the user handbook, the developer onboarding guide, the self-hosting guide and the API reference.

> **Status (2026-10-03): Phase 0 — Foundations.** No product code exists yet. The plan, decisions and first work packages are in place. See [plan/04-roadmap.md](plan/04-roadmap.md).

## Where to start

| You are… | Read this first |
|---|---|
| The project owner | [plan/00-start-here.md](plan/00-start-here.md) |
| An agent about to execute a work package | [AGENTS.md](AGENTS.md), then your work package in [workpackages/](workpackages/README.md) |
| Anyone who wants the big picture | [plan/01-vision-and-fidelity-contract.md](plan/01-vision-and-fidelity-contract.md) and [plan/03-architecture.md](plan/03-architecture.md) |
| Someone checking why a technology was chosen | [adr/README.md](adr/README.md) |
| Anyone asking what they may do with BayanDocs (use, host, integrate, build on it) | [LICENSING.md](LICENSING.md) |

## Map of this repository

| Folder | What lives there |
|---|---|
| [plan/](plan/) | The master plan: vision, requirements, architecture, roadmap, work breakdown, agent workflow, quality and security, risks, owner checklist, learning path, glossary. |
| [adr/](adr/README.md) | Architecture Decision Records. Every significant technical decision, why it was made, and what would make us revisit it. Accepted ADRs are binding on all work. |
| [specs/](specs/README.md) | Technical specifications that several repositories depend on: the document model, the engine protocol, the fidelity lab, font compatibility, the Word feature coverage matrix, the threat model, and Word Behavior Notes. |
| [workpackages/](workpackages/README.md) | Self-contained task briefs that can be handed to an agent, with scope, acceptance criteria and verification steps. |
| `handbook/`, `developer/`, `deploy/`, `api/` | Planned. Created as the product grows (see work package DOCS-001). |

## The repositories

| Repository | Role | Language |
|---|---|---|
| [bayan-core](https://github.com/BayanDocs/bayan-core) | The engine: document model, import/export, text shaping, layout, rendering, PDF, editing logic, proofing, collaboration (CRDT) and encryption. Compiles to native libraries and to WebAssembly. Also hosts the Fidelity Lab tooling. | Rust |
| [bayan-desktop](https://github.com/BayanDocs/bayan-desktop) | The offline desktop application for Windows, macOS and Linux. A thin shell around the engine. | C++20, Qt 6 (Qt Quick/QML) |
| [bayan-web](https://github.com/BayanDocs/bayan-web) | The browser application. A thin shell that runs the WebAssembly engine in a Web Worker. | TypeScript, React |
| [bayan-server](https://github.com/BayanDocs/bayan-server) | The zero-knowledge collaboration server: accounts, sharing, encrypted sync relay, storage. Ships as one container. | Rust |
| [docs](https://github.com/BayanDocs/docs) | This knowledge base. | Markdown |

## License

The engine, desktop app and web app are licensed GPL-3.0-or-later; the server AGPL-3.0-or-later; protocol specifications and integration kits Apache-2.0; this documentation CC BY 4.0. What that means for users, hosts, integrators and contributors is explained in plain language in [LICENSING.md](LICENSING.md); the decision is [ADR-0003](adr/0003-licensing-and-contribution-model.md). License files are being added by work package X-001; until a repository contains its `LICENSE` file, its contents are not yet available under these licenses.
