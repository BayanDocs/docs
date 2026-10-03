# Specifications

Specifications define contracts that more than one crate or repository depends on. They are versioned by their header and changed through pull requests to this repository before the code that implements the change (contract-first, ADR-0002).

| Spec | Version | Owner stream | Consumers |
|---|---|---|---|
| [document-model.md](document-model.md) | v0 (draft, validated by CORE-004) | MODEL | every core crate |
| [engine-protocol.md](engine-protocol.md) | v0 (draft, implemented by CORE-007) | UI / engine | bayan-desktop, bayan-web |
| [fidelity-lab.md](fidelity-lab.md) | v1 | LAB | bayan-core CI, all layout work |
| [font-compatibility.md](font-compatibility.md) | v0 (verified by CORE-008) | TEXT | bayan-fonts, packaging |
| [coverage-matrix.md](coverage-matrix.md) | v1 | all | planning, release notes |
| [threat-model.md](threat-model.md) | v0 (expanded by SRV-003) | SECURITY | all repositories |
| [word-behavior/](word-behavior/README.md) | living | LAB | bayan-text, bayan-layout, bayan-edit |

The sync protocol between core and server is written in Phase 1 (SRV-104) and will be added here.
