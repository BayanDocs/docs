# ADR-0015: Server — single Rust binary, zero-knowledge relay

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Planner (the owner left Rust or Go open)
- **Related:** COL-01…COL-12, OPS-01…OPS-07, PERF-07, ADR-0016, SRV-001…SRV-003, SRV-101…SRV-105

## Context

The server must handle many concurrent WebSocket connections, store and relay encrypted collaboration data, manage accounts, devices, sharing and roles, and be trivially self-hostable ("a simple Docker container"). It must never be able to read documents. The specification allowed Rust or Go.

## Decision

1. **Rust**, same toolchain and policies as the core (ADR-0006, ADR-0017), on **tokio** with **axum** for HTTP and WebSockets.
2. **One binary, one container.** The server also serves the web application's static files, so `docker run` gives a complete deployment. The image is minimal (distroless or scratch), runs as a non-root user with a read-only root filesystem, and is signed with a software bill of materials and provenance attestation.
3. **Storage:**
   - metadata in **SQLite** by default (embedded, zero setup) or **PostgreSQL** for larger deployments, through **sqlx** with versioned migrations;
   - encrypted blobs (update logs, snapshots, media, original packages) on the **local filesystem** by default or any **S3-compatible** object store, behind one storage interface.
4. **Identity:** generic **OpenID Connect** login for organizations (tested with Keycloak, Authentik and Microsoft Entra ID) and **passkeys** (WebAuthn) for standalone accounts. Login credentials are separate from end-to-end encryption keys (ADR-0016).
5. **Roles of the server in MLS:** it acts as the Delivery Service (ordering and fanning out handshake and application messages per group, storing key packages) and supports the Authentication Service role defined in ADR-0016. Handshake messages are sent in MLS's public framing so the server can validate membership changes and enforce role policy; application messages (document updates) are opaque ciphertext to it.
6. **Zero-knowledge invariant:** no server code path receives, stores or derives document keys or plaintext. This is reviewed at every phase gate and in the external audit.
7. **Operations:** configuration via environment variables and a TOML file; secrets from files; Prometheus/OpenTelemetry metrics; structured logs with no content, file names or document titles; health and readiness endpoints; admin CLI and console; backup and restore tooling.
8. **Scale-out (Phase 4):** several instances share PostgreSQL and object storage, with cross-instance fan-out over PostgreSQL `LISTEN/NOTIFY` first and a dedicated message bus only if measurements require it.

## Consequences

- The server can reuse core crates (protocol types, MLS helpers) and shares the owner's single backend language.
- SQLite plus local disk makes small deployments a single container with a single volume.
- Server-side features that need plaintext (search, previews, content in notifications) are impossible by design; clients provide them (ADR-0016).

## Alternatives considered

- **Go:** excellent for network services, but would duplicate MLS and protocol code in a second language and add a language for the owner to learn.
- **Separate services (auth, relay, storage):** more moving parts for self-hosters; rejected for v1.
- **Plaintext server mode for enterprise features:** rejected; compliance needs are met by an organization-controlled escrow member (ADR-0016).

## Revisit when

Load tests show the single-binary design cannot meet PERF-07, or enterprise adopters need deployment topologies the design cannot support.
