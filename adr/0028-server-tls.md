# ADR-0028: Server TLS — rustls with aws-lc-rs, HTTPS through a reverse proxy

- **Status:** Accepted (owner, 2026-10-04)
- **Date:** 2026-10-04
- **Deciders:** Owner, on the recommendation of the SRV-001 implementer session
- **Related:** SEC-01, SEC-05, SEC-12, OPS-01, OPS-05, COL-04, [ADR-0006](0006-rust-core-and-memory-safety.md) (amendment 2026-10-04), [ADR-0015](0015-server-architecture.md), [ADR-0016](0016-e2ee-and-identity.md) (amendment 2026-10-04), [ADR-0017](0017-supply-chain-and-dependency-policy.md) (amendment 2026-10-04), [threat model](../specs/threat-model.md) T9 and T22, SRV-001, SRV-101, SRV-102, SRV-105

## Context

The server needs TLS for its own outbound connections: PostgreSQL in larger deployments (ADR-0015 §3), OpenID Connect discovery and token requests (ADR-0015 §4, SRV-101), and S3-compatible object storage (SRV-102). OPS-01 also requires HTTPS for clients, "via reverse proxy or built-in ACME". SRV-001 shipped without TLS to PostgreSQL because every TLS implementation available to the server's libraries contains C or assembly code, which ADR-0006 does not allow without a decision.

Documents are end-to-end encrypted (ADR-0016), so server TLS protects metadata, credentials and session tokens rather than document content. Those still matter: metadata leakage is threat T9, and an adversary can record encrypted traffic today and decrypt it once a large quantum computer exists ("harvest now, decrypt later", threat T22). Hybrid post-quantum key exchange (X25519MLKEM768: classical X25519 combined with ML-KEM-768 from FIPS 203, so it is never weaker than X25519 alone) protects against that and is already used by default in current browsers.

rustls (Apache-2.0 OR ISC OR MIT) implements the TLS protocol and certificate verification in Rust and delegates cryptographic operations to a pluggable "crypto provider". Facts verified on 2026-10-04:

- **rustls 0.23.45** (2026-09-14) uses **aws-lc-rs** by default and, with its default `prefer-post-quantum` feature, prefers X25519MLKEM768. Its **ring** provider offers only X25519, P-256 and P-384 key exchange. rustls 0.24 (pre-release 0.24.0-dev.1, 2026-07-23) moves providers into separate crates (`rustls-aws-lc-rs`, `rustls-ring`), after which the project plans 1.0.
- **aws-lc-rs 1.18.1** (2026-09-01) wraps **AWS-LC**, Amazon's fork of Google's BoringSSL: C and assembly, maintained by the AWS cryptography team, continuously fuzzed, partly formally verified, with a FIPS 140-3-validated variant. `aws-lc-sys` 0.45.0 is licensed `ISC AND (Apache-2.0 OR ISC) AND Apache-2.0 AND MIT AND BSD-3-Clause AND (Apache-2.0 OR ISC OR MIT) AND (Apache-2.0 OR ISC OR MIT-0)`, all on the ADR-0017 allowlist. The FIPS variant `aws-lc-fips-sys` adds the OpenSSL license, which is not on the allowlist and is generally considered incompatible with the GPL family of licenses. The standard build needs only a C compiler; FIPS builds also need CMake and Go.
- The five RustSec advisories for `aws-lc-sys` (March 2026) concern X.509 name constraints, PKCS#7 verification, CRL scope checks and AES-CCM tag timing, none of which rustls uses from AWS-LC; none were memory-corruption bugs. For comparison, the Rust bindings to OpenSSL (`openssl`, `openssl-src`) have 35 advisories, including use-after-free and buffer overflows. Rust code has had logic bugs too (rustls: 3 advisories; rustls-webpki: 5).
- **ring 0.17.14** (2025-03-11): Rust plus C and assembly derived from BoringSSL, with all parsing in Rust; maintained by the rustls team since RUSTSEC-2025-0007 ("ring is unmaintained") was withdrawn; no post-quantum key exchange; no release since March 2025.
- **graviola 0.4.1** (2026-06-24, by the rustls founder): Rust plus formally verified assembly from s2n-bignum, no C, builds with only the Rust compiler, includes ML-KEM-768. Its README says "This project is very new, so exercise due caution"; no audit is published; it needs AVX2, ADX and BMI2 on x86-64, or the AES, SHA2 and PMULL extensions on aarch64.
- **rustls-rustcrypto** (pure Rust, the RustCrypto family used by OpenMLS's provider) is at 0.0.2-alpha (2024-04-24).
- Library support: sqlx 0.9 hard-codes its provider and offers `tls-rustls-aws-lc-rs` (which always includes `webpki-roots`) or ring variants; reqwest 0.13's `rustls` feature uses aws-lc-rs with the operating system's certificate verifier and has no ring feature; hyper-rustls, object_store's S3 support, instant-acme and rustls-acme default to aws-lc-rs.
- `webpki-roots` (Mozilla's list of trusted root certificate authorities, packaged as a crate) is licensed CDLA-Permissive-2.0, a permissive license for data that is not on the ADR-0017 allowlist.
- Peers: PostgreSQL 18 offers X25519MLKEM768 only if `ssl_groups` includes it (default `X25519:prime256v1`) and it is built with OpenSSL 3.5 or later. Caddy prefers X25519MLKEM768 by default when built with Go 1.24 or later; nginx does with OpenSSL 3.5 or later.
- In rustls's own benchmarks (Q1 2026), rustls with aws-lc-rs outperformed OpenSSL and BoringSSL in most tests; C code here is a safety question, not a speed one.

## Decision

1. **Outbound TLS** from bayan-server (PostgreSQL, OpenID Connect, S3-compatible storage and any future outbound HTTPS) uses **rustls with the aws-lc-rs provider**, standard (non-FIPS) build, with hybrid post-quantum key exchange preferred (rustls's default). The whole server uses this one provider; libraries are configured for it (sqlx `tls-rustls-aws-lc-rs`, reqwest `rustls`, object_store's `aws-lc-rs` feature). ring is not used, so the server carries one crypto provider, not two.
2. **ADR-0006 exception:** AWS-LC is the only C and assembly library allowed in the server besides SQLite, and only as rustls's crypto provider (`aws-lc-sys`, compiled from source by its build script). rustls and its certificate verifier parse all TLS messages and certificates in Rust; server code never calls AWS-LC's own X.509, PKCS#7, CRL or other parsing interfaces. `deny.toml` allows the `cc` build helper only for `libsqlite3-sys` and `aws-lc-sys` and keeps ring, OpenSSL and other native cryptography banned. The exception does not extend to bayan-core, the desktop app or the web app, which do not implement TLS (the core never opens sockets; the shells use Qt's and the browser's).
3. **Certificate verification** is always on: certificates and host names are verified by default (for PostgreSQL, `sslmode=verify-full`), and operators can add a private certificate authority (for example an internal PostgreSQL CA). Libraries that can use the operating system's certificate store (the container's CA bundle) are configured to use it. Where a library only offers Mozilla's list as `webpki-roots`, as sqlx does with aws-lc-rs, that crate is allowed under the ADR-0017 amendment of 2026-10-04.
4. **Inbound HTTPS** terminates at a reverse proxy in front of the server. Documentation and examples recommend **Caddy**: automatic certificates, hybrid post-quantum key exchange by default, written in a memory-safe language (Go), Apache-2.0. The server stays proxy-neutral and the deployment guide lists what any proxy must provide: TLS 1.3 with X25519MLKEM768 offered, WebSocket upgrades (from Phase 3), and forwarding to the server only over the loopback interface or a private network. Whether the server should also terminate HTTPS itself (OPS-01's built-in ACME option) is decided at the Phase-3 gate; if it does, it uses this provider.
5. **FIPS mode is not enabled.** It needs CMake and Go in the build and brings OpenSSL-licensed code; adopting it first requires a licensing decision (ADR-0003, ADR-0017).

## Consequences

- Post-quantum key exchange is used wherever the other side supports it. PostgreSQL operators who want it on the database connection set `ssl_groups` to include X25519MLKEM768 (OpenSSL 3.5 or later); the deployment guide says so.
- The server contains a second C library. Builds take longer and the image grows; the build already has a C compiler for SQLite. The work package that adds TLS records the measured build-time and size increase.
- Using the ecosystem default keeps integration simple: sqlx, reqwest, object_store and the ACME crates need only a feature flag.
- Security alerts for `aws-lc-sys` and `aws-lc-rs` follow the ADR-0017 security-alert session. Because rustls makes the provider swappable, a later move to another provider is a small change.

## Alternatives considered

- **ring:** less C, and parsing stays in Rust, but no post-quantum key exchange, no FIPS path, and reqwest would need its no-provider mode with ring wired in by hand.
- **graviola:** closest to ADR-0006 (no C at all) and post-quantum capable, but self-described as very new, unaudited, limited to CPUs with specific features, and not usable with sqlx 0.9.
- **rustls-rustcrypto:** would match the RustCrypto backend of OpenMLS, but has been a dormant alpha since 2024.
- **OpenSSL (native-tls), SymCrypt and other providers:** more C, including protocol or certificate parsing.
- **TLS in a sidecar process** (stunnel, a service mesh): keeps C out of the server process, but splits the single-container deployment (ADR-0015) and does not cover OpenID Connect.
- **Built-in HTTPS now:** deferred to the Phase-3 gate; Caddy gives the same protection without certificate-management code to maintain.

## Revisit when

- graviola (or another memory-safe provider) publishes an audit or reaches 1.0 and the server's libraries support it, or ring gains post-quantum key exchange.
- An advisory affects AWS-LC code that rustls uses (key exchange, signatures, AEAD), or any memory-safety advisory is published for AWS-LC.
- rustls 1.0 changes how providers are packaged.
- Customers require FIPS-validated cryptography.
- The Phase-3 gate reviews built-in HTTPS.
