# GitHub Settings Baseline

The GitHub settings of the BayanDocs organization and its repositories (who has access, what GitHub Actions may do, how pull requests are merged, which security features are on) are written down as code in [scripts/github-settings.py](../scripts/github-settings.py). The script compares GitHub with that baseline (`audit`) and changes GitHub to match it (`apply`). It covers items 3–6 of the [owner checklist](../plan/09-owner-checklist.md) and the organization settings around them.

Only an organization owner can apply the baseline, with a short-lived token that never leaves their computer. Agent sessions cannot change these settings, and should not: their GitHub access is limited to code and pull requests, and in a test on 2026-10-05 the cloud environment's network proxy replaced a token sent to GitHub's API with the session's own credential and refused requests for GitHub Actions settings. Agents change the baseline in pull requests to this repository; an owner reviews the change and applies it.

## Why settings as code

- **Reviewed and recorded.** A change to the settings is a pull request, reviewed like code, and the history shows what changed, when and why.
- **The same everywhere.** Every managed repository gets the same rules, and a new repository gets them by being added to one list.
- **Drift is visible.** `audit` only reads, so it can run at any time. It reports a setting someone changed by hand, or a repository that is not in the baseline yet, before it matters.

## What the baseline sets

Each value below is a constant near the top of the script, with a comment saying why. The tables summarize them.

### Organization

| Setting | Baseline | Why |
|---|---|---|
| Base permission of members | None | Being a member gives no access by itself; access comes from teams. A future private repository (such as the private corpus, owner checklist item 10) is then not readable by every member. |
| Members can create repositories or GitHub Pages sites | No | Only owners create repositories, so every repository is created knowingly and added to the baseline. |
| Deploy keys | Not allowed | Deploy keys are per-repository SSH keys that act outside anyone's account and two-factor authentication. Nothing uses them; CI publishes the website with GitHub's own short-lived credentials. |
| Two-factor authentication required | Yes, set by hand | GitHub's API can read this setting but not change it. Turning it on removes members and outside collaborators who have not enabled two-factor authentication; the audit lists them (and those who rely on a weak second factor such as SMS) so you can check first. |

### GitHub Actions (every repository; repositories cannot loosen it)

| Setting | Baseline | Why |
|---|---|---|
| Allowed actions | GitHub's own (`actions/*`, `github/*`) plus a reviewed list of third-party actions, empty today | CI is part of the supply chain (threat T16 in the [threat model](../specs/threat-model.md)). Every action is code that runs with access to the repository; each third-party one is added deliberately, in a pull request. |
| Actions must be pinned to a full commit SHA | Yes | [ADR-0017](../adr/0017-supply-chain-and-dependency-policy.md): a version tag can be moved to different code, a commit SHA cannot. GitHub now rejects workflows that break this rule instead of relying on review. |
| Default `GITHUB_TOKEN` permission | Read-only | Each job asks for what it needs in its `permissions:` block ([X-002](../workpackages/phase-0/X-002-ci-security-baseline.md)). |
| Actions can create or approve pull requests | No | A compromised workflow cannot approve its own changes. |
| Workflows from forks of outside contributors | Wait for a maintainer's approval, every time | Nobody's pull request runs code in our CI before a maintainer has looked at it. |
| Workflows on pull requests from forks of private repositories | Never run | There are no private repositories yet; the private corpus may become one, and its contents must not reach anyone's fork through CI. |

### Security features

| Setting | Baseline | Why |
|---|---|---|
| Dependabot alerts | On | An alert starts a security alert session ([plan/06](../plan/06-agent-workflow.md#security-alert-response-session)). |
| Dependabot security update pull requests | Off | ADR-0017: alerts only, never update pull requests; updates happen in batched sessions. |
| Secret scanning and push protection | On | Finds credentials that were committed, and blocks pushes that contain known kinds of secrets. |
| Private vulnerability reporting | On | Security researchers report problems privately (requirement SEC-09; `SECURITY.md` from [X-001](../workpackages/phase-0/X-001-repository-baseline.md) points to it). |
| Immutable releases | On, for every repository of the organization | Once a release is published, its tag and files cannot be changed (owner checklist item 6). One organization-wide setting covers every repository, including ones created later. |

The managed repositories get the other settings directly, so that each one can be checked and fixed on its own. Repositories created later start with the same protection: a security configuration named "BayanDocs baseline" is the default for new public repositories, and repositories cannot override it.

### Teams

Because the base permission is "none", teams are the only way people get access. Both teams start empty; add people to them in the web interface (organization → Teams). GitHub makes the owner who creates a team its first member, which changes nothing for an owner.

| Team | Role in every managed repository | For |
|---|---|---|
| Maintainers | Maintain | Co-maintainers: review and merge pull requests, manage issues and releases. No access to settings. |
| Triage | Triage | Community helpers: label, assign and close issues and pull requests. No write access. |

### Each repository

| Setting | Baseline | Why |
|---|---|---|
| Default branch | `main` | Owner checklist item 1. |
| Merging | Squash merging only; the commit is titled with the pull request's title and keeps the individual commit messages (with their co-author lines) | One commit per pull request on `main`, whose title is the Conventional Commit title of the pull request. |
| Delete branches after merging | Yes | Agent branches (`claude/…`) do not pile up. |
| Offer to update pull request branches | Yes | Needed because a branch must be up to date with `main` before it merges (below). |
| Sign-off on web commits | Required, merges included | GitHub adds a `Signed-off-by:` line for the person who makes a commit in the web interface, and for the person who merges a pull request there. So the squash commit of a pull request merged in the web interface carries the merging person's sign-off, which [ADR-0003 §5](../adr/0003-licensing-and-contribution-model.md#5-contributions) asks for, without anyone pasting it. A merge made through the API (as an agent's merge is) must still end its message with the sign-off. |
| Auto-merge | Off | A person merges each pull request. |
| Wiki | Off | Documentation lives in this repository, where it is reviewed. |

### Rulesets

A ruleset is GitHub's current form of branch protection. Every managed repository gets two.

**"Protect main"** applies to the default branch:

- every change arrives through a pull request, merged by squashing; nobody can push to `main` directly, force-push it or delete it;
- all review conversations must be resolved before merging, and a new push dismisses earlier approvals;
- no approving review is required yet, because GitHub does not let anyone approve their own pull request and agents open pull requests under the owner's account (see "Decisions" below);
- the required checks must have passed, on a branch that is up to date with `main`, and they must come from GitHub Actions, so that nobody can fake a passing check by posting a status with the same name (GitHub Actions is named by its app ID, which every audit looks up and confirms before applying this rule);
- nobody can bypass these rules, owners included.

Because nobody can push to `main` directly, every commit on it is a squash commit that GitHub creates and signs.

The required checks are the CI jobs that run on every pull request. Four of them run in every repository: `DCO`, which checks the Developer Certificate of Origin sign-offs and stays red on a pull request with commits written by an AI agent until the person submitting it adds their own `Signed-off-by:` line to its description, and `REUSE lint`, which checks that every file states its license ([X-001](../workpackages/phase-0/X-001-repository-baseline.md)); `No update bots`, which fails when configuration for Dependabot version updates, Renovate or a similar service appears, and `pip-audit`, which audits the hash-pinned Python tools of CI ([X-003](../workpackages/phase-0/X-003-supply-chain-enforcement.md); both are jobs of `.github/workflows/supply-chain.yml`).

| Repository | Required checks |
|---|---|
| docs | `scripts/verify.sh`, `DCO`, `REUSE lint`, `No update bots`, `pip-audit` |
| bayan-core | `verify (ubuntu-24.04)`, `verify (windows-latest)`, `verify (macos-latest)`, `DCO`, `REUSE lint`, `No update bots`, `pip-audit` |
| bayan-web | `pnpm verify (ubuntu-24.04)`, `pnpm verify (macos-15)`, `pnpm verify (macos-26-intel)`, `DCO`, `REUSE lint`, `No update bots`, `pip-audit` |
| bayan-desktop | `Linux · verification gate`, `Linux · AddressSanitizer and UndefinedBehaviorSanitizer`, `macOS (arm64) · build and test`, `Windows (MSVC) · build and test`, `DCO`, `REUSE lint`, `No update bots`, `pip-audit` |
| bayan-server | `Supply-chain checks`, `Verification gate`, `PostgreSQL integration`, `Container image`, `DCO`, `REUSE lint`, `No update bots`, `pip-audit` |

**"Protect release tags"** applies to tags starting with `v`: they can be created but never moved or deleted, so a version number always names the same code, even for a tag without a published release.

## Running it

You need Python 3.9 or later (on macOS, the `python3` that comes with the Xcode command-line tools is enough) and a clone of this repository at the latest `main`. The script uses nothing outside Python's standard library.

### 1. Create a short-lived token

On github.com, open Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token, and fill in:

- **Token name:** BayanDocs settings.
- **Resource owner:** BayanDocs.
- **Expiration:** 7 days.
- **Repository access:** All repositories.
- **Repository permissions:** Administration, read and write; Contents, read and write. (Metadata, read-only, is added automatically.) Contents is needed only because GitHub shows a repository's merge settings only to tokens that may push to it; the script never reads or changes files, branches or releases.
- **Organization permissions:** Administration, read and write; Members, read and write.

If the organization requires approval for fine-grained tokens, approve your own request under the organization's Settings → Personal access tokens → Pending requests. Never paste the token into a chat, an issue or a file.

### 2. Audit

In a terminal, in your clone of this repository:

```sh
read -rs GH_TOKEN && export GH_TOKEN
python3 scripts/github-settings.py audit
```

The first line waits for you to paste the token without showing it. (Without `GH_TOKEN`, the script asks for the token itself, also without showing it.) The report lists every setting as `ok`, `DRIFT` (differs from the baseline) or `ERROR` (could not be checked; usually a permission missing from the token), plus `info` lines that list who has access (owners, members, outside collaborators, installed apps, people with direct access to a repository, deploy keys) for you to review. Nothing is changed.

### 3. Apply

```sh
python3 scripts/github-settings.py apply
```

The script shows the numbered list of changes it will make and waits until you type `apply`. It then makes them one at a time, a second apart as GitHub asks of clients that make many changes, reports each as done or failed, and audits again. A failed change does not stop the others; fix the cause and run `apply` again, which only makes the changes still needed. `--repo NAME` limits the repository checks to one repository (for example a new one); the organization's settings are always checked.

### 4. Settings that only the web interface can change

The end of every report lists them; check each once:

- **Two-factor authentication** for everyone: organization settings → Authentication security. (The audit checks this one.)
- **Personal access tokens:** require administrator approval for fine-grained tokens, and restrict access by classic tokens: organization settings → Personal access tokens → Settings.
- **Third-party OAuth applications** stay restricted: organization settings → OAuth application policy.
- **Member privileges:** only owners may change repository visibility, delete or transfer repositories, delete issues, and invite outside collaborators: organization settings → Member privileges.

### 5. Delete the token

On github.com: Settings → Developer settings → Personal access tokens → Fine-grained tokens → BayanDocs settings → Delete. Then `unset GH_TOKEN` in the terminal, or close it.

## Changing the baseline

Change the constants near the top of the script in a pull request to this repository, explaining why, and run `apply` after it is merged. Common cases:

- **A new repository:** add it to `REPOSITORIES` with the CI jobs that must pass. Until then, every audit reports it as not in the baseline.
- **A CI job is renamed or added:** update the repository's list in `REPOSITORIES` and apply. Otherwise pull requests wait forever for a check that no longer runs ("Expected — Waiting for status to be reported").
- **A workflow needs a third-party action** (X-002 adds OpenSSF Scorecard, for example): add `owner/repository@*` to the allowed actions list and apply it before merging the workflow; until then GitHub refuses to run it.
- **A second maintainer joins:** add them to the Maintainers team in the web interface, raise `required_approving_review_count` to 1, and set `require_code_owner_review` to true, so that changes to the security-sensitive paths in each repository's `CODEOWNERS` (including `.github/`) need a code owner's approval. Consider then also requiring the DCO check as a workflow that an organization ruleset runs from a pinned commit of a central repository, which a pull request cannot change (see "Decisions" below).

Run `audit` in each monthly dependency session ([plan/06](../plan/06-agent-workflow.md#monthly-dependency-update-session)) and after adding a repository.

## Decisions built into the baseline

These are the choices most likely to need revisiting, with the reason for each.

- **No approving review required.** While the owner is the only maintainer, a required review would block every merge: GitHub does not let anyone approve their own pull request, and pull requests opened by agents count as the owner's. The other merge rules still apply. Revisit when a second maintainer joins.
- **Branches must be up to date before merging.** Two pull requests that each pass on their own can break `main` together; requiring an up-to-date branch prevents that, at the cost of re-running CI after `main` moves. A merge queue would remove that cost later; it needs every required workflow to also run on the `merge_group` event.
- **Nobody can bypass the rules.** In an emergency, an owner changes the baseline in a pull request (or the ruleset in the web interface, then restores it with `apply`), which leaves a record either way.
- **The DCO, REUSE and supply-chain checks judge themselves.** A workflow triggered by a pull request runs the pull request's own copy of `.github/`, so a pull request can change the checks that judge it. Required checks therefore guard against mistakes, not against a malicious pull request; review is the defense, and `.github/` is listed as security-sensitive in every repository's `CODEOWNERS`. A workflow required by an organization ruleset and kept in a central repository would close the gap; revisit it when a second maintainer joins.
- **The squash commit message stays the list of commit messages.** It keeps the agents' `Co-Authored-By:` lines, and the sign-off on web commits adds the merging person's `Signed-off-by:` line at its end. Using the pull request's description as the message instead would leave the description's sign-off before its last lines (the "Generated with" notes), where Git no longer reads it as a trailer.
- **Signed commits are not required.** GitHub can refuse to squash-merge a pull request whose own commits lack a signature it can verify, which would shut out contributors who do not sign their commits, and `main` already holds only commits that GitHub created and signed. Revisit if pull requests ever need to be merged in another way.
- **Code scanning's default setup is off** in the configuration for new repositories, because X-002 adds CodeQL as workflows, and GitHub does not run both kinds of setup in one repository.
- **Base permission "none" and empty teams.** Access is granted explicitly, team by team.

## Troubleshooting

- **`HTTP 403: Resource not accessible by personal access token`:** the token lacks one of the permissions in step 1, or the organization has not approved it yet.
- **`HTTP 404` on an organization address:** the token's resource owner is not BayanDocs.
- **`GitHub rejected the token`:** it expired or was mistyped; create a new one.
- **`CERTIFICATE_VERIFY_FAILED` on macOS** with Python from python.org: run "Install Certificates.command" from that Python's folder in Applications once.
- **Rate limits:** the script waits and retries by itself.

## How the script keeps the token safe

It reads the token only from `GH_TOKEN`, `GITHUB_TOKEN` or a prompt that does not show it; sends it only to `https://api.github.com`; refuses redirects and page links that lead anywhere else; and never prints or stores it. `audit` changes nothing, and `apply` changes nothing until you type `apply`. The script never removes people, never deletes repositories, rulesets or teams, and never touches a repository that is not in the baseline: it lists them for you to decide.
