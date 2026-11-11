# Developing the docs repository

The [docs repository](https://github.com/BayanDocs/docs) is the project's knowledge base: the plan, the architecture decision records (ADRs), the specifications, the work packages and these guides, written in Markdown and built into this website with mdBook ([ADR-0027](../adr/0027-documentation-tooling.md)). This page is the setup map; [CONTRIBUTING.md](../CONTRIBUTING.md) explains how to contribute, and [AGENTS.md §10](../AGENTS.md#10-rules-specific-to-this-docs-repository) gives the rules for writing here. Start with [Getting started](getting-started.md) for Git.

## Platforms

Linux on x86-64. CI runs the gate on Ubuntu 24.04 (`.github/workflows/verify.yml`), and `scripts/dev-setup.sh` downloads Linux x86-64 builds of the tools.

## What you need

- **Git, curl and Python 3**, from [step 1 of Getting started](getting-started.md#step-1-the-base-tools-for-your-system). Python runs the unit tests of the repository's scripts.
- The three tools that `scripts/dev-setup.sh` installs: **mdBook**, which builds the website, **lychee**, which checks the links, and **typos**, which checks the spelling.

## Set up

```sh
git clone https://github.com/BayanDocs/docs.git
cd docs
scripts/dev-setup.sh
```

The script installs the three tools into `.tools/bin` inside the repository (Git ignores that folder), checking every download against its SHA-256. It reads their versions and hashes from `scripts/cloud-environment-setup.sh`, the setup script of the BayanDocs cloud environment, so that your machine, CI and agent sessions run the same versions. `scripts/dev-setup.sh --check` only checks that they are there.

## Run the gate

```sh
scripts/verify.sh
```

Run it before every push. It checks that every Markdown page is in the website's navigation (`SUMMARY.md`), that every ADR and work package ID mentioned exists, and that the vendored Mermaid script is unchanged; builds the website into `book/` (open `book/index.html` to look at it); checks every link between files, `#anchors` included, and every external link (cached for a day); checks the spelling; and runs the unit tests in `scripts/tests/`. It stops early only when a pinned tool is missing or the website does not build; otherwise every check runs even when an earlier one fails, and a summary at the end lists what failed. `scripts/verify.sh --offline` skips only the external links, for a machine without internet access; CI always checks them.

CI runs the same script on every pull request, and the checks shared by every repository; [GitHub Settings Baseline](github-settings.md#rulesets) lists the checks that must pass. The website is published from `main` by `.github/workflows/pages.yml`.

## Deeper notes

- **Writing.** One paragraph per line (no hard line breaks), ATX headings (`#`), relative links to `.md` files, never to folders or to absolute paths of the website, and every new page listed in `SUMMARY.md` ([AGENTS.md §10](../AGENTS.md#10-rules-specific-to-this-docs-repository)). Words that the spelling check does not know, such as project names, go into `typos.toml`.
- **Licenses.** The documentation is CC BY 4.0, the scripts, configuration files and CI workflows MIT-0, and the protocol specifications in `specs/protocols/` Apache-2.0; [CONTRIBUTING.md](../CONTRIBUTING.md#in-this-repository) has the table, and `REUSE.toml` records it for `reuse lint`, which CI runs on every pull request.
- **Decisions and work packages** follow their templates: [adr/0000-template.md](../adr/0000-template.md) and [workpackages/TEMPLATE.md](../workpackages/TEMPLATE.md). An Accepted ADR is changed only by a new ADR or a dated amendment, and the indexes ([adr/README.md](../adr/README.md), [workpackages/README.md](../workpackages/README.md)) are kept in step.
- **pip-audit.** The supply-chain check that every repository shares audits the hash-pinned Python tools of CI; `scripts/dev-setup.sh --pip-audit` installs pip-audit to run that check yourself (`.github/supply-chain/audit_python_tools.py`).
- **Pins.** Every tool of this repository, and of the cloud environment, is pinned in `scripts/cloud-environment-setup.sh`; the [dependency update runbook](dependency-update-runbook.md#docs) says how they move.
