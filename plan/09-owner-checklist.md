# 09 — Owner Checklist: Things Only You Can Do

Agents can write code and documents, but some steps need your accounts, your money, your hardware or your judgement. They are listed in the order they become necessary. Tick them off by editing this file (or ask a planning session to do it).

## Now — before handing off the first work package

- [x] **1. Switch the default branch to `main` in all five repositories.** The repositories were empty, so GitHub treated the first pushed branch (`claude/exciting-mccarthy-rcc9vt`) as the default. `main` has been pushed (2026-10-04); in each repository go to Settings → General → Default branch, switch to `main`, and confirm. Afterwards the old planning branch can be deleted. Done 2026-10-04; the repositories were also made public the same day.
- [ ] **1a. Give agent sessions their tools.** Paste [scripts/cloud-environment-setup.sh](../scripts/cloud-environment-setup.sh) into the BayanDocs cloud environment (the cloud environment menu in a session's title bar → Edit → Setup script). If the environment's network access is **Trusted**, switch to **Custom**, keep the default list of package managers, and add `download.qt.io` and `master.qt.io` (needed only for the desktop app's Qt). Re-paste the script whenever the monthly dependency session updates it. Details: [06-agent-workflow.md](06-agent-workflow.md#cloud-environment-for-agent-sessions).
- [x] **2. Confirm the licensing decision ([ADR-0003](../adr/0003-licensing-and-contribution-model.md)).** Confirmed 2026-10-04: GPL-3.0-or-later for engine, desktop and web; AGPL-3.0-or-later for the server; Apache-2.0 for protocol specifications and integration kits; plain-language FAQ in [LICENSING.md](../LICENSING.md).
- [x] **2a. Decide on the app-store permission ([ADR-0003 §4](../adr/0003-licensing-and-contribution-model.md#4-app-store-permission--in-force)).** Adopted 2026-10-04 and in force with the license files since the same day. It lets BayanDocs be distributed through Apple's App Store (Mac App Store now, iPad and iPhone later) while keeping the source free.
- [ ] **2b. Optional: have an open-source lawyer review the app-store permission wording.** The licenses are in force without a review. If you want one, send the lawyer ADR-0003 §4 and [LICENSING.md](../LICENSING.md) (expect a few hours of their time, or ask organizations that provide legal help to free-software projects), and do it before anyone outside the project contributes: until then you are the only copyright holder and can change the wording on your own.
Items 3–6a are applied by [scripts/github-settings.py](../scripts/github-settings.py), which keeps these settings as code: follow [developer/github-settings.md](../developer/github-settings.md) (create a 7-day token, run `audit`, then `apply`, do the few steps the report says only the web interface can do, then delete the token), and tick 3–6a once `audit` reports no differences. The items below say what the script sets.

- [ ] **3. Protect `main` in each repository** (a ruleset, Settings → Rules → Rulesets): require a pull request before merging (with no approving review while you are the only maintainer, because GitHub does not let anyone approve their own pull request), require the CI checks to pass on a branch that is up to date with `main` (each repository's gate plus `DCO` and `REUSE lint` from X-001), require a linear history, block force pushes and deletions, and allow nobody to bypass the rules. Squash merging only, with the pull request's description, which carries your sign-off, as the commit message (Settings → General → Pull Requests). Commits made in GitHub's web interface are signed off automatically. Release tags (`v*`) can never be moved or deleted.
- [ ] **4. Turn on security alerts only, never update bots** (Settings → Advanced Security), in each repository:
  - enable **Dependabot alerts** (this also gives malware alerts);
  - leave **Dependabot security updates** and grouped security updates **disabled**, and never commit a `.github/dependabot.yml`;
  - enable **secret scanning** and **push protection**;
  - enable **private vulnerability reporting**.
- [ ] **5. Harden GitHub Actions** (Settings → Actions → General), in each repository or once at organization level:
  - require actions to be pinned to a full-length commit SHA;
  - allow only GitHub-authored actions plus an explicit allowlist (agents will propose the list in X-002);
  - set the default `GITHUB_TOKEN` permission to read-only;
  - do not allow Actions to create or approve pull requests;
  - require approval before workflows from outside contributors' forks run.
- [ ] **6. Enable immutable releases** for each repository (release settings), so published release tags and assets cannot be altered.
- [ ] **6a. Restrict access in the organization:**
  - require two-factor authentication for everyone (organization settings → Authentication security; the script checks this but GitHub's API cannot set it, and members without two-factor authentication are removed when you turn it on);
  - set the members' base permission to none, so that access comes only from teams (the script creates two empty ones, Maintainers and Triage), and let only owners create repositories;
  - require approval for fine-grained personal access tokens and restrict classic ones (organization settings → Personal access tokens).
- [ ] **7. Reserve the npm organization `@bayandocs`** (free for public packages) so nobody else can take the scope used for the WebAssembly package.
- [ ] **8. Choose a security contact address** (for example `security@` on a project domain) for `SECURITY.md`. Registering a project domain (for example `bayandocs.org`) is worthwhile now.

## Soon — before Wave 3 of Phase 0

- [ ] **9. Set up the Word reference machine** for the Fidelity Lab (needed by LAB-002, LAB-005 and CORE-008). This is the only proprietary software the project uses, and only as a measuring instrument:
  - a Windows 11 computer or virtual machine dedicated to the lab, holding no personal data, because the corpus will contain documents from the open internet;
  - a Microsoft 365 subscription that includes desktop Word, with the Office build pinned (the Office Deployment Tool can pin a version) so measurements do not drift;
  - LAB-002 lists the exact configuration (macros disabled, AutoSave and cloud integration off, a fixed font set).
  - Optional later: a Mac with Word for spot checks of Word for Mac differences.
- [ ] **10. Decide where the private corpus lives.** Real-world documents found online cannot be redistributed; they need private storage (for example a private S3-compatible bucket or a private repository with Git LFS). LAB-001 proposes options; you choose and create the account.

## Before the first public release (Phase 1)

- [ ] **11. Code signing:**
  - Windows: apply to the SignPath Foundation (free code signing for open-source projects) or buy a commercial certificate;
  - macOS: join the Apple Developer Program (annual fee) for signing and notarization;
  - Linux: create a Flathub account for the Flatpak.
- [ ] **12. Trademark:** run a basic search for "BayanDocs" in your main jurisdictions, register it, and approve the trademark policy an agent drafts. With the GPL licensing, the trademark is what stops others from selling or hosting their versions under the BayanDocs name, so do this before the project becomes widely visible.
- [ ] **13. Community spaces:** enable GitHub Discussions; choose a chat space (for example Matrix); name a Code of Conduct contact.

## Before collaboration GA (Phase 3)

- [ ] **14. External security audit** of the cryptographic design and server. Budget for it, or apply to programmes that fund or provide audits for open-source privacy software.
- [ ] **15. People with lived expertise:** recruit screen-reader users for accessibility testing, native readers of Arabic, Hebrew, Chinese, Japanese and Korean for typography review, and ideally a cryptographer to review the protocol design.

## Funding to consider

Several public programmes fund exactly this kind of open, sovereignty-focused software. Calls and eligibility change, so check current rules before applying: NLnet's NGI Zero funds (EU), the Sovereign Tech Agency (Germany), the Prototype Fund (Germany, individuals), and the Open Technology Fund (privacy and security tools, including security audits). A good application leans on this plan: the Fidelity Contract, zero-knowledge collaboration, and the public Word Behavior Notes as a commons.

## Expected recurring costs

| Item | Why | Rough cost | When |
|---|---|---|---|
| Microsoft 365 with desktop Word, plus a Windows license if using a VM | Fidelity Lab ground truth | A personal or small-business subscription | Phase 0 |
| Apple Developer Program | macOS signing and notarization | Annual membership fee | Phase 1 |
| Windows code signing | SmartScreen reputation, user trust | Free through SignPath Foundation if accepted; otherwise a commercial certificate | Phase 1 |
| Domain name and email | Security contact, website | Small | Now |
| Private corpus storage | Lab | Small | Phase 0–1 |
| External security audits | Collaboration GA, 1.0 | Significant (usually five figures); grants may cover | Phase 3, Phase 6 |
| Font commissioning (Aptos-compatible and other gaps) | Fidelity | Significant per family; grants may cover | Phase 1–4 |

GitHub Actions minutes, including macOS and Windows runners, are free for public repositories.
