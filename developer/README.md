# Developer Guide

These guides are for everyone who works on BayanDocs, people and AI agents alike: how to set up each repository, run its verification gate, and get a change merged. They give the map and the order of the steps; each repository's own `README.md`, `AGENTS.md` and setup script hold the exact commands and versions, and the rules for every contributor are in [AGENTS.md](../AGENTS.md). For the architecture behind the code, read [plan/03-architecture.md](../plan/03-architecture.md).

Start here:

- [Getting started](getting-started.md): the five repositories and how they fit together, the supported platforms, the tools to install on Linux, macOS and Windows, and how to run each repository's verification gate.
- [Your first contribution](first-contribution.md): how work packages, branches, signed-off commits, pull requests and reviews work, for people.

One page for each repository, with its setup notes:

- [Developing bayan-core](bayan-core.md): the Rust engine, its WebAssembly targets and engine artifacts.
- [Developing bayan-desktop](bayan-desktop.md): the C++ and Qt desktop app, its pinned Qt and build tools, and the real engine.
- [Developing bayan-web](bayan-web.md): the TypeScript web app, pnpm, the test browsers and the engine package.
- [Developing bayan-server](bayan-server.md): the Rust server, SQLite and PostgreSQL, and the container.
- [Developing the docs repository](docs.md): the knowledge base and its website.

For maintainers:

- [GitHub Settings Baseline](github-settings.md): the organization's and repositories' GitHub settings as code, and how an owner checks and applies them.
- [Dependency update runbook](dependency-update-runbook.md): the step-by-step procedure for the monthly dependency update session and the security-alert session in each repository, and the checks that enforce the dependency policy.
