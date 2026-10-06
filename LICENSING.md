# Licensing and FAQ

BayanDocs is free and open-source software. This page explains, in plain language, which licenses apply to which parts of the project and what they mean for people who use, host, integrate with, build on, or contribute to BayanDocs. The decision and its reasoning are recorded in [ADR-0003](adr/0003-licensing-and-contribution-model.md).

> **Status:** in force since 2026-10-04. Every repository contains its license files; see [Where the license texts are](#where-the-license-texts-are).

## Licenses at a glance

| Part of BayanDocs | License |
|---|---|
| The engine ([bayan-core](https://github.com/BayanDocs/bayan-core)), the desktop app ([bayan-desktop](https://github.com/BayanDocs/bayan-desktop)) and the web app ([bayan-web](https://github.com/BayanDocs/bayan-web)) | [GNU GPL v3 or later](https://www.gnu.org/licenses/gpl-3.0.html) (GPL-3.0-or-later), with the [BayanDocs App Store Permission](https://github.com/BayanDocs/bayan-core/blob/HEAD/LICENSES/LicenseRef-BayanDocs-App-Store-Permission.txt) |
| The collaboration server ([bayan-server](https://github.com/BayanDocs/bayan-server)) | [GNU AGPL v3 or later](https://www.gnu.org/licenses/agpl-3.0.html) (AGPL-3.0-or-later) |
| Protocol specifications ([specs/protocols/](specs/protocols/README.md)), the protocol definitions crate (`bayan-core/crates/bayan-protocol/`) and the integration kits (`bayan-server/integrations/`) | [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) (Apache-2.0) |
| Documentation (this repository, except the protocol specifications) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); code snippets in documentation also [MIT-0](https://spdx.org/licenses/MIT-0.html), and scripts, configuration files and CI workflows MIT-0 only |
| Contribution tooling in every repository: the `.github/` folder (CI workflows, the DCO check, pull request and issue templates), `.editorconfig` and `.gitattributes` | [MIT-0](https://spdx.org/licenses/MIT-0.html), so anyone may reuse it in any project ([ADR-0003, amendment of 2026-10-06](adr/0003-licensing-and-contribution-model.md#amendment-2026-10-06-mit-0-for-the-shared-contribution-tooling)) |
| Templates, sample content, default styles and anything else the apps copy into your documents | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (no rights reserved) |
| Fonts created by the project | [SIL Open Font License 1.1](https://openfontlicense.org/) |
| The name "BayanDocs" and its logo | Trademark policy (not a copyright license; published before the first public release) |

## What you may do, and what you must do

| You want to… | What you must do |
|---|---|
| Use BayanDocs (desktop, web or server) for anything, including in a business, government or school | **Nothing** |
| Create, publish or sell documents made with BayanDocs | **Nothing.** Your documents are yours, including content that came from our templates (CC0). |
| Run the unmodified server for your organization, or host it for others, free or paid | **Nothing,** beyond keeping the built-in "Source code" link working |
| Connect any client to a BayanDocs server | **Nothing** |
| Build an integration that talks to BayanDocs through its documented protocols and APIs | **Nothing.** If you redistribute code from our Apache-2.0 integration kits, keep their license notices. |
| Write your own client or server that speaks the BayanDocs protocols | **Nothing.** The specifications and protocol definitions are Apache-2.0. |
| Change configuration settings | **Nothing** |
| Redistribute copies of BayanDocs, unmodified or modified | Pass on the license and make the matching source code available |
| Modify the desktop or web app and distribute or host it | Make your modified source code available to your users under the GPL. Serving the web app to browsers counts as distributing it. |
| Modify the server and let other people use it over a network | Offer those users your modified source code under the AGPL; pointing the "Source code" link at it is enough |
| Build BayanDocs code into your own program | Your program must be released under the GPL (or the AGPL, for server code), with its source code, when you distribute it. This is not possible in a closed-source product. |
| Call your version "BayanDocs" or use our logo | Only as the trademark policy allows. Modified versions must use a different name; they may say they are based on BayanDocs. |

## Frequently asked questions

### Using BayanDocs

**Can my company use BayanDocs for commercial work?** Yes. Every open-source license, including ours, allows use for any purpose. Using the apps or running a server creates no obligations at all.

**Does the GPL apply to the documents I write?** No. Licenses of the software do not cover what you create with it. The templates, sample content and default styles we ship are released under CC0, so even content copied from them into your documents carries no conditions.

### Running a server

**Can we host BayanDocs for other people, and charge for it?** Yes. If you run it unmodified, you have nothing to publish; the built-in "Source code" link already points your users to the exact source of the version you run. If you modify the server and let others use it over a network, the AGPL requires you to offer those users your modified source code.

**What counts as modifying the server?** Changing its source code. Configuration files, environment variables and choosing among the storage or identity options the server offers are not modifications. Separate programs that talk to the server through its documented protocols and APIs are not modifications either.

**Why does BayanDocs show a "Source code" link?** It makes license compliance automatic. For an unmodified installation the link is already correct; operators of modified versions only need to point it at their own source code.

### Integrating with BayanDocs

**Can we connect our document management system, identity provider, storage or other tools?** Yes. Integrations that communicate with BayanDocs through its documented protocols and APIs are separate programs, and the GPL and AGPL do not apply to them.

**Do our integrations have to be open source?** No. The protocol specifications, the protocol definitions crate and the integration kits are licensed under Apache-2.0, a permissive license that you can use in proprietary software; it asks only that you keep its notices, and it includes a patent license from contributors.

**Our company policy does not allow AGPL software. Can we still integrate?** Yes. The Apache-2.0 integration kits contain no AGPL code. Whether your policy allows you to *run* an unmodified AGPL server is for your legal team to decide; the AGPL itself imposes no obligations on unmodified use.

**Can we build our own BayanDocs-compatible client?** Yes, from the Apache-2.0 specifications and protocol definitions, under any license you choose. You cannot copy GPL or AGPL BayanDocs code into it unless your client is released under a compatible license. Connecting to a particular server still requires an account on it, each new device must be approved by its user, and each server's administrators decide which devices and applications may connect.

### Building on BayanDocs code

**Can I use the BayanDocs engine in my own product?** Yes, if your product is free software released under the GPL (version 3 or later) and you share its source code when you distribute it. You cannot use BayanDocs code in a closed-source product. This is deliberate: it keeps everyone's contributions free.

**Can BayanDocs be distributed through Apple's App Store?** Yes. The GPL on its own conflicts with Apple's App Store terms, so the engine and apps carry an additional permission, the [BayanDocs App Store Permission](https://github.com/BayanDocs/bayan-core/blob/HEAD/LICENSES/LicenseRef-BayanDocs-App-Store-Permission.txt) ([ADR-0003 §4](adr/0003-licensing-and-contribution-model.md#4-app-store-permission--in-force)), that allows distribution through app stores as long as the source code stays freely available to everyone.

**Can I sell BayanDocs?** The GPL allows charging for copies, but you must provide the source code, and anyone who receives it may share it freely. You may not use the BayanDocs name or logo for your version without permission under the trademark policy.

### Contributing

**Under which license are my contributions made?** Under the license of the files or directory you change ("inbound = outbound"); for the engine and the apps that includes the app-store permission. Changes to the shared contribution tooling (`.github/`, `.editorconfig` and `.gitattributes`) are MIT-0 in every repository. You certify that you have the right to contribute with a Developer Certificate of Origin sign-off. There is no contributor license agreement, so nobody, including the project itself or any future owner of it, can relicense your contribution.

**What about contributions written with AI assistance?** Agents never sign off on their own; the human who submits the work certifies it (see [ADR-0003 §5](adr/0003-licensing-and-contribution-model.md#5-contributions)).

## Where the license texts are

| Repository | License of the repository (SPDX) | Other areas |
|---|---|---|
| [bayan-core](https://github.com/BayanDocs/bayan-core) | `GPL-3.0-or-later WITH LicenseRef-BayanDocs-App-Store-Permission` | `crates/bayan-protocol/`: `Apache-2.0`; `.github/`, `.editorconfig`, `.gitattributes`: `MIT-0`; `CODE_OF_CONDUCT.md` (the Contributor Covenant): `CC-BY-4.0` |
| [bayan-desktop](https://github.com/BayanDocs/bayan-desktop) | `GPL-3.0-or-later WITH LicenseRef-BayanDocs-App-Store-Permission` | `.github/`, `.editorconfig`, `.gitattributes`: `MIT-0`; `CODE_OF_CONDUCT.md` (the Contributor Covenant): `CC-BY-4.0` |
| [bayan-web](https://github.com/BayanDocs/bayan-web) | `GPL-3.0-or-later WITH LicenseRef-BayanDocs-App-Store-Permission` | `.github/`, `.editorconfig`, `.gitattributes`: `MIT-0`; `CODE_OF_CONDUCT.md` (the Contributor Covenant): `CC-BY-4.0` |
| [bayan-server](https://github.com/BayanDocs/bayan-server) | `AGPL-3.0-or-later` | `integrations/`: `Apache-2.0`; `.github/`, `.editorconfig`, `.gitattributes`: `MIT-0`; `CODE_OF_CONDUCT.md` (the Contributor Covenant): `CC-BY-4.0` |
| [docs](https://github.com/BayanDocs/docs) (this repository) | `CC-BY-4.0` | `specs/protocols/`: `Apache-2.0`; `scripts/`, configuration files and CI workflows (listed in `REUSE.toml`): `MIT-0` |

In every repository, `LICENSE` holds the official text of the main license, so GitHub shows it; the `LICENSES/` folder holds the full text of every license used in the repository; and `REUSE.toml` records which license applies to which files, in the machine-readable [REUSE](https://reuse.software) format that license scanners understand. The Apache-2.0 folders also contain their own `LICENSE` file, so they can be copied out on their own.

## The fine print

This FAQ explains how the BayanDocs project understands its licenses and what it intends. It is not legal advice; the license texts are authoritative. Questions are welcome in the project's discussions or issue tracker.
