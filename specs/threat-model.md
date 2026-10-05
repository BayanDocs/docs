# Threat Model — v0

- **Status:** v0 (initial, from the planning session). SRV-003 expands it into v1 with full data-flow diagrams for the server, sync and encryption; every phase gate reviews it.
- **Owner stream:** SECURITY
- **Method:** data-flow-based analysis with STRIDE categories (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege).
- **Related:** SEC-01…SEC-12, ADR-0006, ADR-0015, ADR-0016, ADR-0017, ADR-0023, ADR-0028, [plan/07](../plan/07-quality-security-testing.md)

## 1. Assets

| Asset | Why it matters |
|---|---|
| Document content (text, media, comments, history) | The core confidentiality promise |
| Document metadata (titles, folder structure, authorship) | Often as sensitive as content |
| Cryptographic keys (identity, device, group, recovery) | Compromise breaks confidentiality and integrity |
| Account credentials and sessions | Access to the server and sharing |
| Collaboration metadata (who works with whom, when, how much) | Visible to the server by necessity; must be minimized |
| Software integrity (binaries, updates, web code, extensions) | A compromised build defeats every other control |
| Service availability | Teams depend on the server |
| Fidelity Lab private corpus | Contains third-party documents; must not leak |

## 2. Adversaries

| Adversary | Capabilities | In scope |
|---|---|---|
| Malicious document author | Crafts files to exploit parsers or abuse active content | Yes |
| Malicious or compromised collaborator | Holds a legitimate role; sends crafted CRDT updates; abuses sharing | Yes |
| Malicious or compromised server operator | Full control of server, database, storage, and the web code it serves | Yes (confidentiality and integrity of content must hold; availability cannot be guaranteed) |
| Network attacker | Observes and modifies traffic | Yes |
| Supply-chain attacker | Publishes malicious package versions, compromises CI actions or toolchains | Yes |
| Malicious script or extension | Runs inside the automation sandbox | Yes |
| Passive metadata observer | Sees traffic timing and sizes | Partially (documented residual risk) |
| Attacker with full control of a user's unlocked device | Reads everything that user can read | Out of scope (endpoint security) |

## 3. Trust boundaries

1. File bytes → engine parsers.
2. Engine ↔ shell (C ABI, Web Worker messages).
3. Shell ↔ operating system or browser (clipboard, fonts, URLs, files).
4. Client ↔ server (WebSocket and HTTP).
5. Server ↔ database and object storage.
6. Engine ↔ automation sandbox and extensions.
7. Engine ↔ AI sidecar process.
8. Build and release pipeline → users (binaries, packages, containers, web assets).
9. Web origin → browser (delivery of the web application's code).

## 4. Principal threats and mitigations

| # | Boundary | STRIDE | Threat | Mitigations | Status |
|---|---|---|---|---|---|
| T1 | 1 | E, D | Memory-corruption exploit in a parser (ZIP, XML, fonts, images, EMF) | Rust with `forbid(unsafe_code)`; no C parsers; fuzzing; resource limits (ADR-0006) | Planned |
| T2 | 1 | E, I | Active content: macros, DDE, OLE, remote templates, external links, dangerous URL schemes, UNC credential leaks | Never auto-run or auto-fetch; consent per document (ADR-0023) | Planned |
| T3 | 1 | D | Decompression bombs, entity expansion, deep nesting, giant tables | DTDs rejected; limits on sizes, ratios, depth, counts; cancellable layout | Planned |
| T4 | 2 | E, D | Malformed messages from a compromised shell component or web page script | Schema validation at the boundary; no panics across boundary; strict CSP and Trusted Types on web | Planned |
| T5 | 4 | I | Server reads document content | E2EE with MLS; zero-knowledge invariant (ADR-0016) | Planned |
| T6 | 4 | S, E | Server adds a device or member to read documents ("ghost member") | Cross-signed device keys verified by clients; membership changes in public framing, visible and verifiable; safety numbers; key transparency later | Planned |
| T7 | 4 | T, E | Collaborator without write role (or the server) injects edits | Role roster in signed group context; server rejects; clients verify sender role before import | Planned |
| T8 | 4 | D, E | Crafted CRDT updates crash or exhaust a client | Updates authenticated before import; resource limits; fuzzed import; import isolated in the worker on web | Planned |
| T9 | 4 | I | Metadata leakage (membership, timing, sizes) | Titles and structure encrypted; minimal server metadata; documented residual risk; padding options later | Partially mitigated |
| T10 | 4 | I | Deleted content persists in collaboration history and leaks to new members | New members receive a snapshot without prior history by default; history retention policy; "inspect document" removes history; exported `.docx` contains no CRDT history unless the user opts in | Planned |
| T11 | 9 | T, I | Malicious server serves modified web code to steal keys | Desktop as high-assurance client; Subresource Integrity enforced with `Integrity-Policy`; reproducible builds with published hashes; adopt web code transparency when available | Residual risk documented |
| T12 | 4, 5 | S | Account takeover through weak login | Passkeys; OIDC with organization policies; session hardening; rate limits | Planned |
| T13 | 4, 5 | D | Abuse: update flooding, storage exhaustion | Quotas, rate limits, role revocation, per-group limits | Planned |
| T14 | 6 | E, I | Script or extension escapes sandbox or exfiltrates content | Pure-Rust engine with no ambient authority; capability prompts; WebAssembly component isolation; limits | Planned (Phase 5) |
| T15 | 7 | E | Compromised AI sidecar or model file | Separate process; models verified by hash or signature; no network access by default | Planned (Phase 5) |
| T16 | 8 | T | Malicious dependency or CI compromise | ADR-0017: 24-hour minimum age, exact pins, audits, SHA-pinned actions, minimal permissions, provenance, signing | Planned (Phase 0) |
| T17 | 8 | T | Malicious update delivered to users | Signed releases; signed update metadata with rollback protection; immutable releases | Planned |
| T18 | 3 | I | Clipboard or URL handling leaks content to other apps or sites | Explicit user actions only; confirmation before opening URLs; no automatic external fetch | Planned |
| T19 | lab | I | Private corpus leaks | Private storage; aggregate-only reports; isolated reference machine | Planned |
| T20 | 2, logs | I | Content leaks via logs, crash reports or recordings | No content in logs; opt-in, user-reviewed crash reports; recordings only on explicit request | Planned |
| T21 | 4 | S, T, D, E | Third-party or modified clients, buggy or malicious, connect with a user's valid credentials | Server treats every client as untrusted (validation, limits, quotas, rate limits, fuzzed decoders); a new device needs approval from an existing trusted device and optionally an administrator; clients verify every update's signature and sender role; device lists with revocation; optional administrator policy on client applications (not a security boundary); public conformance suite (SEC-13, COL-13, COL-14) | Planned |
| T22 | 4, 5 | I | Harvest now, decrypt later: an adversary records TLS traffic, or keeps MLS ciphertext (a hostile server operator keeps all of it), and decrypts it once a large quantum computer can break today's key exchange | Hybrid post-quantum key exchange (X25519MLKEM768) on the server's TLS connections and at the recommended reverse proxy (ADR-0028); collaboration ships only with the hybrid post-quantum MLS ciphersuite (ADR-0016, amendment 2026-10-04); symmetric algorithms such as AES are not meaningfully affected | Planned |

## 5. Accepted residual risks (v0)

- A server operator can deny service and observe collaboration metadata.
- Users of the web application must trust the origin that serves it until web code transparency ships in browsers; self-hosting or the desktop app removes third-party trust.
- A collaborator with read access can copy content; encryption cannot prevent that.
- Compromised endpoints are out of scope.
- A user can run any client software with their own account, including a careless or malicious one; it can do only what that user may do, and the user or an administrator can revoke the device.

## 6. Open items for SRV-003

1. Full data-flow diagrams for login, device enrollment, sharing, link sharing, sync, snapshotting and recovery.
2. Exact metadata stored by the server, field by field, with justification.
3. Role enforcement design details and failure modes (server and client disagree).
4. Recovery kit and passkey PRF flows; lost-device and revocation scenarios.
5. Compliance escrow member design and its abuse cases.
6. Security requirements checklist per server endpoint.
