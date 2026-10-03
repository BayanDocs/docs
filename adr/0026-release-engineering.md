# ADR-0026: Release engineering, signing and updates

- **Status:** Accepted (details finalized in X-101 and DESK-104)
- **Date:** 2026-10-03
- **Deciders:** Planner
- **Related:** SEC-06, PLT-01…PLT-03, ADR-0002, ADR-0017, X-101, DESK-104, WEB-103

## Context

Users must be able to trust that what they install is what the project built, and updates must not become an attack vector. Facts verified on 2026-10-03: GitHub supports immutable releases (generally available since 2025-10-28) and artifact attestations; crates.io and npm support trusted publishing from CI.

## Decision

1. **Versioning:** Semantic Versioning; 0.x until 1.0; release notes include fidelity scores and any layout-epoch change.
2. **Channels:** nightly (automated, unsigned for testing), beta and stable (signed).
3. **Integrity:** every release artifact has a SHA-256 checksum, a software bill of materials (CycloneDX), and a build provenance attestation; releases are immutable; packages are published to crates.io and npm with trusted publishing and provenance.
4. **Signing:**
   - Windows: Authenticode, through the SignPath Foundation (free for open source) or a commercial certificate;
   - macOS: Developer ID signing and notarization;
   - Linux: Flatpak through Flathub as the primary channel; AppImage, `.deb` and `.rpm` with signatures;
   - containers: keyless Sigstore signatures plus SBOM and provenance.
5. **Updates:** platform-native mechanisms first (Flathub, Windows package managers, Microsoft Store and MSIX if adopted, Sparkle-style signed appcasts on macOS). Any custom updater must verify signed metadata with rollback and freeze-attack protection (The Update Framework model). Updates never install without user consent unless an administrator configures it.
6. **Reproducible builds:** a goal from Phase 1 and a requirement by 1.0, verified by rebuilding releases in CI.
7. **Server deployments:** versioned container images, database migrations that run automatically with documented rollback, and a supported-version policy.

## Consequences

- Release automation is a real work stream (X-101) rather than an afterthought.
- Some costs are unavoidable (Apple developer membership; possibly a Windows certificate).

## Alternatives considered

- **Unsigned binaries:** blocked by operating-system defenses and unacceptable for a security-focused product.

## Revisit when

Platform signing or store policies change.
