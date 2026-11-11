# Your first contribution

This page walks a person through a first contribution to BayanDocs, in any of its five repositories: where planned work is described, how to branch and commit, what a pull request needs, and how it is reviewed and merged. It is an overview: the rules themselves are in [AGENTS.md](../AGENTS.md), which binds every contributor, people as much as AI agents, and in the `CONTRIBUTING.md` of each repository ([the docs repository's](../CONTRIBUTING.md); the others carry the same rules).

## 1. Read the rules

- **[AGENTS.md](../AGENTS.md)**: the canonical rules for every contributor. Accepted decisions are binding, a change stays within its scope, the verification gate passes before every push, dependencies follow strict rules, and every input is treated as hostile.
- **The repository's `CONTRIBUTING.md`**: commit messages, the Developer Certificate of Origin, licensing and the dependency rules, as they apply to that repository.
- **The [Code of Conduct](../CODE_OF_CONDUCT.md)**, which everyone who takes part follows.
- **Security problems are reported privately**, never in a public issue: [SECURITY.md](../SECURITY.md) says how.

## 2. Find something to work on

- **Small fixes**, such as a typo, a broken link or an obvious bug, can go straight to a pull request.
- **Larger changes start with an issue** (a bug report or a feature request) in the repository concerned, so that they can be planned.
- **Planned work is described in work packages.** Each [work package](../workpackages/README.md) is a brief with its scope, deliverables and acceptance criteria, and becomes one pull request; the index shows each one's status. Most work packages are carried out by AI agent sessions, which the owner, or the orchestrator on the owner's behalf, starts, and a separate reviewer session reviews each of their pull requests ([plan/06](../plan/06-agent-workflow.md), [plan/12](../plan/12-orchestration.md)). If you would like to take one on, say so in an issue first.
- **Decisions are recorded.** Accepted [architecture decision records (ADRs)](../adr/README.md) are binding. To change a decision, propose a new ADR, or an amendment, in a pull request to the docs repository, and wait until it is accepted before building on it.
- **A change across repositories starts with its contract**: first the specification in the docs repository, then bayan-core, then the shells or the server ([ADR-0002](../adr/0002-repository-topology-and-contracts.md) §2).

## 3. Set up and check the repository

Follow [Getting started](getting-started.md) and the repository's developer page, and run its verification gate once on a fresh clone of `main`, before you change anything: then you know that any failure afterwards comes from your change.

## 4. Branch and commit

- **Work on a branch**, in your fork of the repository (or in the repository itself, if you have access). Nobody can push to `main` directly, owners included: every change reaches it through a pull request ([GitHub Settings Baseline](github-settings.md#rulesets)).
- **Keep commits small and logical**, and stay within what the issue or work package asks for. Note anything else you find as a follow-up instead of changing it, and do not reformat or refactor code you are not otherwise changing.
- **Write commit messages as [Conventional Commits](https://www.conventionalcommits.org/)**, such as `fix(opc): reject ZIP entries with absolute paths` ([CONTRIBUTING.md](../CONTRIBUTING.md#commit-messages-and-pull-request-titles)).
- **Sign off every commit** with `git commit --signoff`. Your sign-off certifies, under the [Developer Certificate of Origin](../CONTRIBUTING.md#developer-certificate-of-origin), that you have the right to submit the change under the license of the files it changes. That section of CONTRIBUTING.md explains what the sign-off certifies, how to add a forgotten one, and how commits written with an AI assistant are signed off; the DCO check enforces it on every pull request.
- **Test what you change.** Every behavior change comes with tests, and every bug fix with a test that would have caught the bug; a change to layout output also needs Fidelity Lab evidence. Never weaken, skip or delete a test or a check to make a change pass ([AGENTS.md §4](../AGENTS.md#4-the-verification-gate-is-sacred)).
- **A new dependency needs a justification** in the pull request: what it does, why we cannot reasonably write it, the alternatives, its license, its maintenance, the publish date of its version and what it brings in ([AGENTS.md §5](../AGENTS.md#5-dependencies-strict--see-adr-0017)). Routine upgrades happen only in the monthly dependency session.
- **Every file states its license**, in its own SPDX header or in the repository's `REUSE.toml`; `reuse lint` checks it ([CONTRIBUTING.md](../CONTRIBUTING.md#licensing-of-contributions)).

## 5. Open a pull request

1. **Run the gate** before every push.
2. **Open a pull request against `main`.** Its title becomes the title of the commit on `main`, so write it as a Conventional Commit too.
3. **Fill in the template**, which is the [hand-off template](../plan/06-agent-workflow.md#hand-off-template): what changed and why, the work package, evidence for each acceptance criterion, the commands you ran, dependencies, deviations, follow-ups, open questions and notes for whoever works on it next. Write it in plain language: not every reviewer knows every language the project uses.
4. **Wait for CI.** The workflows of a pull request from an outside contributor's fork run only after a maintainer has looked at it and approved the run, every time. Then the repository's gate runs, with the checks that every repository shares: the DCO sign-off, `reuse lint`, the supply-chain checks, the workflow lint and CodeQL. [GitHub Settings Baseline](github-settings.md#rulesets) lists, for each repository, the checks that must pass before a pull request can merge.

## 6. Review and merge

- **Review.** A reviewer checks the pull request against its work package, the ADRs and the rules ([plan/06](../plan/06-agent-workflow.md)). Answer every review comment: all review conversations must be resolved before the pull request can merge, and a new push dismisses earlier approvals.
- **Up to date with `main`.** A pull request merges only when its branch is up to date with `main` and the required checks have passed on it. GitHub's "Update branch" button brings it up to date; the merge commit it makes adds nothing of its own, so it needs no sign-off.
- **Merging.** Every pull request is squash-merged: it becomes a single commit on `main`, titled with the pull request's title, and its branch is deleted. The owner decides whether to merge a pull request with commits by other people than the owner and the project's agents ([plan/12](../plan/12-orchestration.md#what-only-the-owner-decides)), and its authors sign off their commits themselves.
- **Afterwards.** If the pull request completed a work package, the work package is marked Done in the [index](../workpackages/README.md).
