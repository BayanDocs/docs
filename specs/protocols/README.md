# Protocol specifications (Apache-2.0)

This folder holds the specifications of the protocols and APIs that clients and integrations use to talk to a BayanDocs server.

**License:** unlike the rest of this repository (CC BY 4.0), everything in this folder is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) (SPDX: `Apache-2.0`). Anyone may implement these protocols in software under any license, and Apache-2.0 includes a patent license from contributors ([ADR-0003](../../adr/0003-licensing-and-contribution-model.md), [LICENSING.md](../../LICENSING.md)).

**Rules for this folder:**

- Specifications describe behavior; they never copy text or code from the GPL engine or the AGPL server.
- Machine-readable companions (JSON Schemas, API descriptions) live in the Apache-2.0 areas `bayan-core/crates/bayan-protocol/` and `bayan-server/integrations/`.
- Changes follow the contract-first rule (ADR-0002): the specification changes here before the implementations change.

## Index

| Specification | Status | Work package |
|---|---|---|
| `sync-protocol.md`: client ↔ server synchronization of encrypted updates, snapshots, presence and resumption | Planned (Phase 1) | SRV-104 |
| `server-api.md`: accounts, devices, sharing, administration and automation APIs, with machine-readable descriptions in `bayan-server/integrations/` | Planned (Phases 1–3) | SRV-101, SRV-103, SRV-105 |
