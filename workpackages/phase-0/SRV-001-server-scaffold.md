# SRV-001: Server scaffold, container and CI

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | SERVER |
| Repository | bayan-server |
| Attach to session | bayan-server, docs |
| Size | M |
| Depends on | — |
| Unblocks | SRV-002, X-003, Phase-1 server work |
| Status | Ready |
| Requirements | ARC-06, OPS-01, OPS-02, OPS-03, SEC-04 |
| Decisions | ADR-0015 (implement it), ADR-0006, ADR-0017, ADR-0025 |
| Specs | [threat-model.md](../../specs/threat-model.md) |

## Context

The server is a single Rust binary shipped as one minimal container, with SQLite by default and PostgreSQL optional (ADR-0015). It follows the same toolchain, lint and dependency conventions as the core (mirror CORE-001's choices where they apply). The SQLite library is C code; it is acceptable under ADR-0006 because it only processes the server's own metadata through bound parameters, never untrusted documents or SQL text, and this must be stated in the pull request.

## Objective

A runnable, minimal, hardened server skeleton with configuration, logging, database migrations, a container image and CI, ready for identity, storage and relay work.

## Scope

### In scope

- Cargo workspace mirroring the core's conventions: pinned toolchain, edition 2024, exact `[workspace.dependencies]`, `forbid(unsafe_code)`, strict Clippy, `cargo xtask verify`, `deny.toml`, `.cargo/config.toml` with the minimum publish age.
- axum application on tokio with `/healthz`, `/readyz` and `/version`; request IDs; request body size limits and timeouts; graceful shutdown.
- Typed configuration from environment variables and an optional TOML file, with secrets read from files (`*_FILE` convention); validation with clear errors; documented in `docs/` of this repository or the README.
- Structured logging with `tracing` (JSON output option) and a **content-free policy**: a test proves request bodies, authorization headers, cookies and query strings are never logged.
- Database layer with sqlx: SQLite (bundled) by default and PostgreSQL behind configuration; versioned migrations (initial migration only); offline query metadata committed so builds do not need a live database.
- Static file serving of a configurable directory (future web app) with the security headers from ADR-0014.
- Container: multi-stage `Dockerfile` with builder image pinned by digest; final image distroless or scratch; non-root user; works with a read-only root filesystem and a writable `/data` volume; a `healthcheck` subcommand used by the container health check; OCI labels. `compose.yaml` for local development.
- CI: `cargo xtask verify`; container build; smoke test running the container read-only and checking `/healthz`; image vulnerability scan with a scanner chosen and pinned with justification.
- Update this repository's `AGENTS.md` and `README.md` with real commands.

### Out of scope

Accounts, storage of documents, WebSockets, MLS (later WPs).

## Deliverables

Workspace, server skeleton, migrations, container files, CI, documentation.

## Acceptance criteria

- [ ] AC-1 CI green: verify gate, container build, smoke test, scan (no high or critical findings, or each explained).
- [ ] AC-2 The container runs as non-root with a read-only root filesystem (demonstrated in CI).
- [ ] AC-3 The logging test proves sensitive request data is never logged.
- [ ] AC-4 The server starts with SQLite by default and with PostgreSQL when configured (integration test using a PostgreSQL service container in CI).
- [ ] AC-5 Image size reported; all dependencies pinned, at least 24 hours old, allowlisted and justified.

## Verification

`cargo xtask verify`; CI links; `docker run` commands documented.

## Escalate if

A dependency requires C code beyond SQLite, or the scanner reports issues in the base image that cannot be resolved by choosing another pinned image.
