# Phase 1 — Faithful Viewer: server work packages (drafts)

**Status: Draft**, refined at the Phase-0 gate after SRV-003 (threat model v1). Server work runs in parallel with the viewer because the zero-knowledge server does not depend on the layout engine. All in bayan-server; attach bayan-server and docs (bayan-core read-only where shared crates are involved).

### SRV-101 — Identity: OIDC, passkeys, sessions, devices
- **Size:** L · **Depends on:** SRV-001, SRV-003 · **Decisions:** ADR-0015, ADR-0016
- **Scope:** generic OpenID Connect login (tested with Keycloak, Authentik and Microsoft Entra ID); passkey accounts (WebAuthn); session management with secure defaults; device registration (public keys only); admin bootstrap; rate limits; audit log of security events (no content).

### SRV-102 — Storage layer
- **Size:** M · **Depends on:** SRV-001
- **Scope:** metadata schema (users, devices, documents, groups, memberships, roles, quotas) with migrations for SQLite and PostgreSQL; blob store interface with filesystem and S3-compatible backends (dependency chosen by size and maintenance); quotas; encrypted-blob APIs (opaque bytes only).

### SRV-103 — MLS delivery and authentication services; WebSocket relay
- **Size:** L · **Depends on:** SRV-002, SRV-101, SRV-102 · **Decisions:** ADR-0016
- **Scope:** key-package store; per-group ordering and fan-out of handshake and application messages; public-state validation of commits and role enforcement on authenticated connections; WebSocket gateway with authentication, backpressure, reconnection and resumption; retention policy.

### SRV-104 — Sync protocol specification v1 and reference client
- **Size:** M · **Depends on:** SRV-103, CORE-004
- **Scope:** write `specs/sync-protocol.md` (contract-first): message types, ordering, resumption, snapshots, compaction by clients, presence; implement a Rust reference client used by tests and later by bayan-core's `bayan-sync`.

### SRV-105 — Operations
- **Size:** M · **Depends on:** SRV-001
- **Scope:** Prometheus and OpenTelemetry metrics; structured security audit log; backup and restore tooling with tests; compose profiles (SQLite single node; PostgreSQL plus S3-compatible storage); load-test harness and first PERF-07 measurements.
