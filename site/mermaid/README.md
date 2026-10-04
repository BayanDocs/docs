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
| Licenses | MIT for Mermaid. The code it bundles is under MIT, ISC, BSD-3-Clause, Apache-2.0 (Chevrotain, inside Mermaid's parser) and MPL-2.0 OR Apache-2.0 (DOMPurify), all on the ADR-0017 allowlist. [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt) lists every package with code in the file and its copyright notices; the repository's `REUSE.toml` records the license expression. Both come from [scripts/mermaid-licenses.py](../../scripts/mermaid-licenses.py). |

**Why not Mermaid 12.** Mermaid 12.0.0 (2026-09-10) and 12.1.0 (2026-10-02) bundle the ELK layout engine (elkjs, licensed EPL-2.0) into `mermaid.min.js`. EPL-2.0 is not on the license allowlist in [ADR-0017](../../adr/0017-supply-chain-and-dependency-policy.md), so the site stays on the 11.x line until either the owner amends the allowlist or Mermaid moves ELK back out of the main bundle. The monthly dependency session should re-check this. Mermaid has published fixes for older major versions before (10.9.8 on 2026-08-04), and the website only renders diagrams written by this project, so staying on 11.x is low-risk.

**What is inside the file, and why a script lists it.** `mermaid.min.js` is one file built from about seventy packages, and some of those were themselves prebuilt with code from other packages: Mermaid's own parser (`@mermaid-js/parser`) carries langium, Chevrotain and the vscode-languageserver libraries, cytoscape carries `heap` and parts of `lodash`, venn.js carries `fmin`, and roughjs carries its four helper packages. A dependency-tree listing such as `pnpm licenses list` cannot see those, because they are only development dependencies of the packages that carry them. It also shows packages whose code is not in the file: the build drops code that Mermaid does not use, so `robust-predicates` (Unlicense, not on the allowlist), `d3-delaunay`, `delaunator`, several other d3 packages and Node.js-only helpers are in the tree but not in the file. [scripts/mermaid-licenses.py](../../scripts/mermaid-licenses.py) therefore reads the build's own records: the source file named before each module in `dist/mermaid.js` (the unminified build published next to `mermaid.min.js`), skipping modules whose code was dropped, and the source maps published next to prebuilt files. Prebuilt files without a source map are looked at by a person, and the result is recorded in the script's `REVIEWED` table; the script stops when a bundled package version has not been reviewed.

## How it is used and checked

- `book.toml` adds [mermaid-init.js](mermaid-init.js) to every page. On pages that have a diagram, it loads `mermaid.min.js` with a Subresource Integrity hash, so the browser refuses a file that does not match. Pages without diagrams never download Mermaid. Mermaid runs with `securityLevel: "strict"`, and diagrams follow the reader's light or dark theme.
- [scripts/verify.sh](../../scripts/verify.sh) checks that `mermaid.min.js` matches [SHA256SUMS](SHA256SUMS) and that the hash in `mermaid-init.js` matches the file.

## How to update (monthly dependency session only)

1. Find the newest version published at least 24 hours ago: `curl -s https://registry.npmjs.org/mermaid` and read the `time` field.
2. Run `python3 scripts/mermaid-licenses.py X.Y.Z`. It downloads that release from npm and checks it against the registry's integrity hash, refuses a release younger than 24 hours or one that bundles the ELK layout engine (see "Why not Mermaid 12"), lists every package with code in `mermaid.min.js`, and checks every license against the ADR-0017 allowlist. If it stops with a list of prebuilt files that have no source map, look inside each file for code from other packages (no imports of other packages yet functions that come from them, license comments, the package's `dependencies` and `devDependencies` in its `package.json`), record what you find in `REVIEWED` in the script, and run it again.
3. Run `python3 scripts/mermaid-licenses.py X.Y.Z --write`. It installs the release's `mermaid.min.js` here (the bytes it checked), updates [SHA256SUMS](SHA256SUMS) and `MERMAID_INTEGRITY` in [mermaid-init.js](mermaid-init.js), and rewrites [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt). If it reports "TO DO" lines, make those changes by hand: the license expression for `mermaid.min.js` in `REUSE.toml`, and any new license text in `LICENSES/` (added with `reuse download`). Run the script once more without `--write`: it must report every file as up to date and no "TO DO".
4. Update the table above (version, publish date and npm integrity value) and the version in the comment above the Mermaid entry in `REUSE.toml`.
5. Run `scripts/verify.sh`, which builds the site into `book/`. Serve it with `python3 -m http.server --directory book 8000`, open a page with diagrams (such as `http://localhost:8000/plan/03-architecture.html`), and check that the diagrams render in a light and a dark theme.
