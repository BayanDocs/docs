# Mermaid diagrams on the website

The Markdown in this repository contains Mermaid diagrams (code blocks marked `mermaid`). GitHub draws them natively. On the mdBook website they are drawn by a pinned copy of Mermaid kept in this folder. This note records why it was done this way (work package [DOCS-001](../../workpackages/phase-0/DOCS-001-knowledge-base-site.md), as [ADR-0027](../../adr/0027-documentation-tooling.md) asked), what exactly is pinned, and how to update it.

## The choice: a vendored script, not a preprocessor

ADR-0027 left two options open, to be chosen by dependency cost:

- **A pinned, vendored copy of the Mermaid script (chosen).** One dependency (Mermaid itself), stored as one file whose checksum is recorded and checked. Nothing extra runs at build time, and the Markdown keeps plain `mermaid` code blocks, so GitHub and the website read the same source.
- **An mdBook preprocessor such as mdbook-mermaid.** It still sends the same Mermaid script to readers' browsers, so it would add a second dependency on top of the first: a Rust program with its own dependency tree that would have to be pinned, checksum-verified, kept compatible with our mdBook version and updated every month.

The vendored script is therefore strictly cheaper.

## What is pinned

| Item | Value |
|---|---|
| Package | `mermaid` 11.17.2 from npm, published 2026-08-25T11:52:39Z |
| npm tarball integrity | `sha512-V6K3C8EBdEsPFZXSKMJe6ppQOENxuHARr9GvHX4hh47lAbhMRD9qf4oEK7LoaRQxULMa80/qt5gHO73aCleBBg==` (checked against the registry when the file was copied) |
| File | `mermaid.min.js`, the package's `dist/mermaid.min.js`, unmodified |
| SHA-256 of the file | recorded in [SHA256SUMS](SHA256SUMS) |
| Subresource Integrity hash | `MERMAID_INTEGRITY` in [mermaid-init.js](mermaid-init.js) |
| Licenses | MIT for Mermaid; the bundled packages are MIT, ISC, BSD-3-Clause and MPL-2.0 OR Apache-2.0, all on the ADR-0017 allowlist. Listed in [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt) and recorded in the repository's `REUSE.toml`. |

**Why not Mermaid 12.** Mermaid 12.0.0 (2026-09-10) and 12.1.0 (2026-10-02) bundle the ELK layout engine (elkjs, licensed EPL-2.0) into `mermaid.min.js`. EPL-2.0 is not on the license allowlist in [ADR-0017](../../adr/0017-supply-chain-and-dependency-policy.md), so the site stays on the 11.x line until either the owner amends the allowlist or Mermaid moves ELK back out of the main bundle. The monthly dependency session should re-check this. Mermaid has published fixes for older major versions before (10.9.8 on 2026-08-04), and the website only renders diagrams written by this project, so staying on 11.x is low-risk.

**Code that is in the dependency tree but not in the file.** Mermaid's dependency tree also contains `robust-predicates` (Unlicense, not on the allowlist). Its code is not in `mermaid.min.js`: the build leaves it out, and the file contains none of its constants (`134217729`, `11102230246251565e-32`) or the names of the packages that use it (`Delaunay`, `delaunator`).

## How it is used and checked

- `book.toml` adds [mermaid-init.js](mermaid-init.js) to every page. On pages that have a diagram, it loads `mermaid.min.js` with a Subresource Integrity hash, so the browser refuses a file that does not match. Pages without diagrams never download Mermaid. Mermaid runs with `securityLevel: "strict"`, and diagrams follow the reader's light or dark theme.
- [scripts/verify.sh](../../scripts/verify.sh) checks that `mermaid.min.js` matches [SHA256SUMS](SHA256SUMS) and that the hash in `mermaid-init.js` matches the file.

## How to update (monthly dependency session only)

1. Find the newest version published at least 24 hours ago: `curl -s https://registry.npmjs.org/mermaid` and read the `time` field. Skip major versions whose bundle contains code under a license outside the allowlist (see "Why not Mermaid 12").
2. Download the tarball named in that version's `dist.tarball` and check it against `dist.integrity`: `echo "sha512-$(openssl dgst -sha512 -binary mermaid-X.Y.Z.tgz | base64 -w0)"` must print the same value.
3. Check the licenses. In a scratch directory outside this repository, run `pnpm add mermaid@X.Y.Z --ignore-scripts` and `pnpm licenses list --prod`. Every license must be on the ADR-0017 allowlist, or its code must be shown to be absent from `dist/mermaid.min.js` (as for `robust-predicates` above). Also search the file for `org.eclipse.elk`, which must not appear. Update [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt), and update `REUSE.toml` and `LICENSES/` (with `reuse download`) if the set of licenses changed.
4. Copy `package/dist/mermaid.min.js` here unchanged. Update [SHA256SUMS](SHA256SUMS) (`sha256sum mermaid.min.js > SHA256SUMS`), the `MERMAID_INTEGRITY` hash in [mermaid-init.js](mermaid-init.js) (`echo "sha384-$(openssl dgst -sha384 -binary mermaid.min.js | base64 -w0)"`), and the table above.
5. Run `scripts/verify.sh`, then open the built site (`book/plan/03-architecture.html`, for example, through `mdbook serve`) and check that the diagrams render in a light and a dark theme.
