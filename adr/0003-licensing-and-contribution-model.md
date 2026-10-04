# ADR-0003: Licensing and contribution model

- **Status:** Accepted (owner confirmed 2026-10-04). The licenses, including the §4 app-store permission, are in force since 2026-10-04; a legal review of §4 is optional.
- **Date:** 2026-10-03 (proposed); 2026-10-04 (accepted with changes; in force)
- **Deciders:** Owner (decision); Planner (analysis)
- **Related:** [LICENSING.md](../LICENSING.md) (plain-language FAQ), X-001, ADR-0013, ADR-0017, OPS-08

## Context

The owner's goals, in order:

1. BayanDocs is completely free and open source.
2. Nobody can take contributors' work into a closed product or a closed hosted service.
3. Companies can still use BayanDocs and integrate with it, and corporate contributors are not driven away.

Facts that shape the choice:

- **No open-source license forbids making money.** Commercial use is part of the Open Source Definition (criterion 6) and of the Free Software Definition (freedom 0); it includes ordinary use at work. Licenses that forbid commercial use or competing offerings (PolyForm Noncommercial, Commons Clause, BSL, SSPL, FSL, Elastic License) are source-available, not open source: they would stop businesses and governments from using BayanDocs, keep it out of Linux distributions, and disqualify it from most public open-source funding. Goal 2 is therefore met with **copyleft** (anything built from our code stays open), **trademark** (only we can use the name), and **no CLA** (nobody can ever relicense contributors' work), not by forbidding commerce.
- **GPL is broadly accepted by companies** (the Linux kernel is the most corporate-contributed open-source project). **AGPL** is the license most often banned by corporate policies, but it is the only widely used open-source license that covers modified software offered as a network service.
- **Web client code is distributed** to every user's browser, so the GPL's source obligations already apply to anyone hosting a modified web app; the AGPL adds coverage for server-side modifications.
- **Licensing is effectively permanent** once outside contributions arrive, because there is no CLA.
- **Compatibility:** Qt's LGPLv3 modules (dynamically linked) work with GPLv3; our MIT, Apache-2.0, BSD and MPL-2.0 dependencies can be included in GPLv3 and AGPLv3 works; GPLv3 section 13 explicitly permits combining GPLv3 and AGPLv3 code, so the server can use core crates; Apache-2.0 code can be included in GPL and AGPL works (not the reverse).

## Decision

### 1. Licenses

| What | License (SPDX) |
|---|---|
| bayan-core (except the Apache-2.0 area below) | GPL-3.0-or-later |
| bayan-desktop | GPL-3.0-or-later |
| bayan-web | GPL-3.0-or-later |
| bayan-server (except the Apache-2.0 area below) | AGPL-3.0-or-later |
| Protocol specifications for talking to a BayanDocs server: `docs/specs/protocols/` | Apache-2.0 |
| Protocol definitions crate: `bayan-core/crates/bayan-protocol/` | Apache-2.0 |
| Integration kits: `bayan-server/integrations/` (machine-readable API descriptions, SDKs, examples) | Apache-2.0 |
| Documentation (everything else in the docs repository) | CC-BY-4.0; code snippets in documentation also MIT-0 |
| Templates, sample content, default styles and any other material the apps copy into users' documents | CC0-1.0 |
| Fonts created by the project | OFL-1.1 |

**In force since 2026-10-04.** Each repository contains `LICENSE` (the official text of its main license, from gnu.org or creativecommons.org, so GitHub recognizes it), a `LICENSES/` folder with the full text of every license it uses (from the SPDX License List data, version 3.29.0, identical to what `reuse download` fetches), and `REUSE.toml`, which records which license applies to which files. The Apache-2.0 folders that exist also hold their own `LICENSE` file, so they can be copied out on their own.

### 2. Rules for the Apache-2.0 areas

- They never contain, copy from, or depend on GPL or AGPL code. They are written against the specifications so that anyone can use them in software under any license.
- The GPL and AGPL implementations may depend on them.
- An **integration** communicates with BayanDocs through its documented protocols and APIs. Linking BayanDocs engine or server code into another program is not an integration; it makes that program subject to the GPL or AGPL.
- **Third-party clients and integrations** may connect to BayanDocs servers, as with any open protocol. What they can do is governed by accounts, device approval, roles and server limits (SEC-13, COL-13, OPS-09), never by which software they are. Keeping the protocols closed would not prevent this, because the GPL clients already show how the protocols work.

### 3. Making compliance easy

- The web app and the server show a **"Source code" link** to the exact source of the running version (OPS-08). Operators of modified versions comply by pointing it at their own source.
- [LICENSING.md](../LICENSING.md) publishes a plain-language FAQ. It states that using BayanDocs for any purpose, running the unmodified server, connecting clients and building integrations through the documented protocols and APIs carry no obligations (beyond keeping the built-in source link working, and keeping Apache-2.0 notices when redistributing kit code).

### 4. App-store permission — in force

**Problem.** The GPL forbids anyone distributing the software from imposing further restrictions on recipients (GPLv3 section 10). Apple's App Store terms impose such restrictions, so distributing GPL software there violates the license, and any single copyright holder can force removal. This happened to VLC in 2011. VideoLAN then had to contact a large number of past contributors to relicense before VLC returned to Apple's store in 2013. Windows, Linux and Android stores carry no such conflict in practice, and Mac users can always install from our website.

**Mechanism.** GPLv3 section 7 lets copyright holders attach an **additional permission** to their code. Only copyright holders can grant it, so it must be in place before anyone outside the project contributes; afterwards, every contributor would have to agree.

**Decision (owner, 2026-10-04).** Attach a one-paragraph permission to bayan-core, bayan-desktop and bayan-web, allowing distribution through app stores as long as the source code stays freely available to everyone. The owner put the text below into force on 2026-10-04 without waiting for a legal review. Its canonical copy is `LICENSES/LicenseRef-BayanDocs-App-Store-Permission.txt` in each of those three repositories.

> **BayanDocs App Store Permission (version 1.0).** Additional permission under section 7 of the GNU General Public License, version 3: the copyright holders of BayanDocs give you permission to convey this program, or any work based on it, in object code form through an application distribution service even if the terms, usage rules or technical measures of that service would otherwise be further restrictions prohibited by section 10 of the GNU General Public License, provided that you (a) make the Corresponding Source of what you convey available at no charge to everyone who receives it through that service, under the GNU General Public License version 3 or any later version, by means outside the service if the service does not permit it; (b) state in the service's listing, or in the program itself, that the program is free software under the GNU General Public License and where its Corresponding Source can be obtained; and (c) impose no restriction of your own on recipients' exercise of the rights granted by the GNU General Public License beyond those the service itself requires. This permission covers only code whose copyright holders have granted it. As section 7 provides, you may remove this permission from your copies of the work or any part of it.

**Identifier.** In REUSE metadata (`REUSE.toml` and file headers) the license of these repositories is written `GPL-3.0-or-later WITH LicenseRef-BayanDocs-App-Store-Permission`, the form the REUSE tool (6.2) accepts. SPDX 3.0 names custom additions `AdditionRef-…`, and Rust tooling such as cargo-deny accepts only that form, so package manifests use `GPL-3.0-or-later WITH AdditionRef-BayanDocs-App-Store-Permission`. Both name the same text. Once REUSE supports `AdditionRef-`, rename the file and use that form everywhere.

**Consequences.**
- A Mac App Store build, and a future iPad or iPhone app (tablet editing is planned for Phase 6), become possible.
- Anyone, including a fork, may use the permission, but they must still publish their source and cannot use the BayanDocs name.
- Third-party GPL code that lacks the same permission cannot go into components shipped through app stores; the dependency allowlist (ADR-0017) already excludes copyleft dependencies.
- A custom permission may prompt a one-time review by some companies' license scanners. A legal review of its wording is optional (see Timing).

**Timing.** The permission had to be in place before the first outside contribution, because only copyright holders can grant it; it is in force since 2026-10-04. Until the first outside contribution, the owner, as the only copyright holder, can still change its wording freely, so that is the best time for an optional legal review. Afterwards, broadening it would need every contributor's consent, while anyone may still remove it from their own copies (GPLv3 section 7).

### 5. Contributions

- **Inbound = outbound:** a contribution is licensed under the license of the files or directory it changes, certified by the Developer Certificate of Origin. **No contributor license agreement.** Nobody, including the project itself or a future owner of it, can relicense contributors' work.
- **AI-assisted contributions:** the DCO is a certification only a person can make. Commits authored by AI agents carry the agent's attribution trailers and are **not** signed off by the agent. The human who submits or merges the work (initially the owner) certifies the DCO for them, by a sign-off line in the pull request description and in the squash-merge commit. Human-authored commits are signed off by their human author as usual. X-001 implements the DCO check accordingly.
- **REUSE compliance:** every file carries SPDX license and copyright information, either in its own header or through the repository's `REUSE.toml` (a default for the repository plus declarations for the Apache-2.0 and CC0 areas); `reuse lint` passes in every repository and is checked in CI (X-001).

### 6. Trademark

The BayanDocs name and logo are governed by a trademark policy (drafted before the first public release) and should be registered (owner checklist). Modified versions must use a different name; they may say they are based on BayanDocs.

## Consequences

- Nobody can ship a closed product built on BayanDocs code. Anyone hosting a modified BayanDocs must publish their changes: the GPL covers the web app they serve, the AGPL covers server changes.
- Companies can use BayanDocs and build integrations without copyleft obligations. The documents users create are entirely theirs.
- The engine cannot be embedded in proprietary software (intended).
- Companies with blanket AGPL bans may not run or contribute to the server; integrations built from the Apache-2.0 kits contain no AGPL code.
- **Accepted gap:** a modified engine used only on its operator's own servers (for example a paid conversion service) need not be shared, because the GPL has no network clause. Closing it would require the AGPL for the engine and its corporate friction.
- Copyleft relies on copyright; purely AI-generated code may receive thin copyright protection, which makes human authorship (direction, review, edits) and the trademark more important.
- The licenses can never be changed without the consent of every contributor.

## Alternatives considered

- **MPL-2.0 for core, desktop and web (this ADR's original proposal, 2026-10-03):** maximizes embedding of the engine, but lets companies build closed products around it; rejected by the owner for that reason.
- **Apache-2.0 or MIT everywhere:** maximum adoption, but allows closed forks and closed hosted services.
- **AGPL-3.0 everywhere:** closes the conversion-service gap, at the cost of the most corporate friction, and forces any website embedding the engine to open its whole application.
- **LGPL-3.0 for the engine:** its relinking requirement is awkward with Rust static linking, WebAssembly bundles and app stores.
- **EUPL-1.2 for the server:** covers online access and is popular with European public bodies, but its compatibility clause can let combined code move to a license without the network clause, and it is little known in US companies; AGPL kept, with the mitigations in §2 and §3.
- **OSL-3.0 for the server:** has a network clause, but cannot be combined with the GPL engine.
- **Source-available licenses (BSL, SSPL, FSL, PolyForm, Commons Clause):** not open source; see Context.
- **Dual licensing with a CLA:** would allow selling commercial licenses, but requires contributors to trust a single owner with relicensing power.

## Revisit when

An optional legal review of §4 recommends changes (ideally before the first outside contribution); the REUSE tool supports SPDX 3.0 `AdditionRef-` identifiers; the first outside contribution is about to be accepted (after which this decision is effectively permanent).

## History

- 2026-10-03: proposed MPL-2.0 for core, desktop and web; AGPL-3.0-or-later for the server.
- 2026-10-04: the owner chose GPL-3.0-or-later for core, desktop and web so contributors' work cannot become part of closed products; kept AGPL-3.0-or-later for the server; added Apache-2.0 protocol specifications and integration kits and the licensing FAQ; added CC0 for material copied into users' documents; proposed the app-store permission.
- 2026-10-04 (later): the owner adopted the app-store permission (§4), subject to legal review of its final wording; clarified that third-party clients are governed by authentication, device approval and roles (§2).
- 2026-10-04 (later still): the owner put the licenses and the app-store permission (version 1.0) into force without waiting for a legal review, which stays optional; `LICENSE`, `LICENSES/` and `REUSE.toml` were added to all five repositories.
- 2026-10-04 (DOCS-001): the owner chose MIT-0, as for `scripts/`, for the docs repository's configuration files and CI workflows (`book.toml`, `lychee.toml`, `typos.toml`, `.gitignore`, `.github/`) and the website's Mermaid loader script (`site/mermaid/mermaid-init.js`), because CC BY 4.0 is meant for prose rather than code; `REUSE.toml` lists the files.
