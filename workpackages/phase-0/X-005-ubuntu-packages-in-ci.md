# X-005: Ubuntu packages in CI — exact files on a pinned base, from more than one source

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | SECURITY |
| Repository | bayan-desktop, bayan-web, docs |
| Attach to session | `docs`, `bayan-desktop` and `bayan-web`, all three with push access |
| Size | M |
| Depends on | X-003, X-004 (both Done); the [amendment of 2026-11-05 to ADR-0017](../../adr/0017-supply-chain-and-dependency-policy.md#amendment-2026-11-05-ubuntu-packages-in-ci), accepted |
| Unblocks | The monthly dependency sessions of bayan-desktop and bayan-web ([plan/12 §7](../../plan/12-orchestration.md#7-specialty-sessions)), which then move the new pins |
| Status | Kept in the [work package index](../README.md) |
| Requirements | SEC-05 |
| Decisions | ADR-0017 (amendments of 2026-10-04, tools in agent sessions, and 2026-11-05, Ubuntu packages in CI), ADR-0025 |
| Specs | [threat-model.md §11](../../specs/threat-model.md#11-principal-threats) (T16) |

## Context

Some CI jobs install Ubuntu packages: libraries, and the development files of libraries ("-dev" packages: the headers and link files a compiler needs), that a build or the tests need and that GitHub's runner image does not carry. They take them from snapshot.ubuntu.com, which serves Ubuntu's package archive as it was at a fixed moment, so that every run gets the same versions, signed by Ubuntu (ADR-0017). At today's `main` branches (docs `b05b966`, bayan-desktop `a59bea6`, bayan-web `130bf57`; bayan-server `4c5ea45` and bayan-core `4ff6165` install no Ubuntu packages) there are three such places:

- **bayan-desktop:** the two Linux jobs of `.github/workflows/ci.yml` ([line 57](https://github.com/BayanDocs/bayan-desktop/blob/a59bea602d1df30d47dd9aa863a7e0c52b9cdc9e/.github/workflows/ci.yml#L57) and [line 102](https://github.com/BayanDocs/bayan-desktop/blob/a59bea602d1df30d47dd9aa863a7e0c52b9cdc9e/.github/workflows/ci.yml#L102)) and the C++ analysis job of `.github/workflows/codeql.yml` ([line 162](https://github.com/BayanDocs/bayan-desktop/blob/a59bea602d1df30d47dd9aa863a7e0c52b9cdc9e/.github/workflows/codeql.yml#L162)) run `apt-get update --snapshot "$UBUNTU_SNAPSHOT"` and `apt-get install --snapshot "$UBUNTU_SNAPSHOT" $UBUNTU_PACKAGES`: six -dev packages that Qt needs (`libgl-dev libegl-dev libvulkan-dev libxkbcommon-dev libfontconfig-dev libdbus-1-dev`), at `UBUNTU_SNAPSHOT: 20261027T000000Z`. [tests/workflows/test_ubuntu_packages.py](https://github.com/BayanDocs/bayan-desktop/blob/a59bea602d1df30d47dd9aa863a7e0c52b9cdc9e/tests/workflows/test_ubuntu_packages.py) keeps the two workflows' values equal.
- **bayan-web:** `scripts/dev-setup.sh` ([`APT_SNAPSHOT=20261025T000000Z`](https://github.com/BayanDocs/bayan-web/blob/130bf5752dec081a3ad6ae5fc2b11a0a35809a77/scripts/dev-setup.sh#L30) and [`setup_browser_libraries`](https://github.com/BayanDocs/bayan-web/blob/130bf5752dec081a3ad6ae5fc2b11a0a35809a77/scripts/dev-setup.sh#L286)) installs those of 79 libraries that the Playwright browsers need and that the machine lacks. CI's `pnpm verify (ubuntu-24.04)` job runs it ([ci.yml, line 86](https://github.com/BayanDocs/bayan-web/blob/130bf5752dec081a3ad6ae5fc2b11a0a35809a77/.github/workflows/ci.yml#L86)), and so do developers and, when bayan-web is attached to a session, the agent environment.
- **docs:** [scripts/cloud-environment-setup.sh](../../scripts/cloud-environment-setup.sh) (`step_apt`) installs the same six -dev packages and ShellCheck in the agent environment, at `APT_SNAPSHOT=20261003T000000Z`.

The [dependency update runbook](../../developer/dependency-update-runbook.md) asks to keep the four dates equal. Today they differ (2026-10-27, 2026-10-25 and 2026-10-03), because bayan-desktop moved its date twice outside the monthly session ([bayan-desktop#8](https://github.com/BayanDocs/bayan-desktop/pull/8), [bayan-desktop#9](https://github.com/BayanDocs/bayan-desktop/pull/9)) and left the others to the next monthly session.

### How it fails

Between 2026-10-04 and 2026-11-05, 21 of the 198 attempts of these install steps failed (the orchestrator's count from the Actions API; re-runs count as attempts), for two reasons.

**1. The runner image is newer than the frozen date ("skew"): 8 failures, all in bayan-desktop.** GitHub rebuilds its `ubuntu-24.04` image about once a week with Ubuntu's security updates: 11 versions from 20260810 to 20261026, by the [history of the image's readme](https://github.com/actions/runner-images/commits/main/images/ubuntu/Ubuntu2404-Readme.md). A -dev package requires exactly the version of its library that was current at the frozen date. When the runner already has a newer, fixed version of the library, apt would have to downgrade it, refuses, and stops with "unmet dependencies":

- `libfreetype-dev : Depends: libfreetype6 (= 2.13.2+dfsg-1ubuntu0.1) but 2.13.2+dfsg-1ubuntu0.2 is to be installed`, in both Linux jobs of a pull request on 10-17 (run `39055195605`, attempt and re-run), in the C++ analysis of the same pull request, and in the weekly C++ analysis of 10-20 and 10-27;
- `libbrotli-dev : Depends: libbrotli1 (= 1.1.0-2build2) but 1.1.0-2ubuntu0.1`, in the weekly C++ analysis of 11-03 (run `41654130562`).

Downgrading the library is not an option: it would remove security fixes. This planning session reproduced the failure in a container: on the `ubuntu:24.04` image of 2026-10-25, the snapshot of 2026-10-03 fails with `zlib1g-dev : Depends: zlib1g (= 1:1.3.dfsg-3.1ubuntu2.2) but 1:1.3.dfsg-3.1ubuntu2.3 is to be installed`, while the snapshots of 2026-10-25 and 2026-10-27 install. Runtime libraries are exposed too, only less often: the 385 packages that bayan-web's 79 libraries bring into a bare Ubuntu image include 56 dependencies on an exact version, such as `libpam-systemd` on `systemd (= 255.4-1ubuntu8.18)` and `systemd` on `libsystemd0` of the same version; bayan-web has escaped so far because it installs only what the runner lacks.

The agent environment carries the same risk. Its image (Ubuntu's minimized image, serial 20261024.1, with packages added on 2026-10-27) already holds the security updates of FreeType, zlib and Brotli, together with their -dev packages. The setup script's snapshot of 2026-10-03 still worked there on 2026-11-03 only because none of the packages it had to install depended on the exact versions of those libraries.

**2. snapshot.ubuntu.com is down: about 9 failures, mostly in bayan-web.** From about 11:45 UTC on 2026-11-04 until 2026-11-05, with short recoveries, its dated snapshots answered 401, 502 or 503, while archive.ubuntu.com answered normally. bayan-web's install step failed in 7 attempts with apt's `Err:` on the snapshot's InRelease file or metadata:

- the nightly runs of 11-04 and 11-05 (`41826136179`, `42025815758`);
- the run on `main` after a merge, and its one allowed re-run (`41836056589`, attempts 1 and 2);
- a pull request on 11-04 (`41823795008`);
- earlier, with the snapshot of 2026-10-03, a pull request on 10-14 (`38570537024`, attempt 2) and the nightly run of 10-10 (`38045414556`).

In bayan-desktop the sanitizer job got a 503 on 10-14 (`38526184743`), and the C++ analysis of the same push failed in the same minute (its log is gone). bayan-web's step also failed 3 times without a log left (10-11, 10-14, 10-20), and once because Playwright's download server could not be found (10-21), which is not Ubuntu's doing. Running the jobs in a container alone (option A below) does not help here, because the container would still download from the snapshot.

Successful install steps take, as medians: 59 s in bayan-desktop's Linux jobs (at most 303 s, 77 steps), 92 s in its C++ analysis (336 s, 22 steps), and 158 s for bayan-web's whole set-up step, which also installs Node.js, pnpm and the browsers (1047 s, 75 steps).

### The design

Two changes remove the two failure modes, and a cache makes the second one rarer still.

1. **A pinned base.** Each Linux job that installs Ubuntu packages runs in a container (`container:` in the workflow): a separate, isolated Ubuntu system on the runner, started from an image. The image is a Docker Official Image of Ubuntu 24.04 pinned by its digest (the SHA-256 of its contents, so the same reference always gives the same image): `docker.io/library/buildpack-deps:noble-scm@sha256:…`, Ubuntu's own image plus tools such as ca-certificates, curl and git, so that a job can check out its history and download over HTTPS before anything else is installed. The packages are installed on this fixed base instead of the runner image, so a newer runner image changes nothing. The snapshot date is chosen on or after the base image's creation, and the monthly session moves the base and the date together. This is option A of bayan-desktop#9's follow-up.
2. **Exact files, from more than one source.** Each repository commits a lock file, which the monthly session generates by running apt in the pinned base against the snapshot. It lists every package file to install, with its path in Ubuntu's archive (the "pool"), its size and its SHA-256, all taken from Ubuntu's signed package index, and the order in which apt would unpack and configure them. In CI, an installer downloads each file and checks its size and SHA-256. Because the hash proves the file, its source does not matter: the installer tries the snapshot at the lock's date first, then Launchpad's librarian (the file store of Launchpad, the service that builds Ubuntu's packages, which keeps the files of the packages Ubuntu has published), then the live archive. It moves to the next source only when a download fails, and stops at the first mismatch without trying another source, as bayan-core's [spike fonts](https://github.com/BayanDocs/bayan-core/blob/4ff61658a48bc07d3c5f9062a903044a7de80bff/spikes/text-pipeline/fonts/fetch.sh#L50) do. Then it installs the files with dpkg, Debian's low-level package tool, in apt's recorded order, without apt, without a package index and without network.
3. **A cache of verified files.** `actions/cache` keeps the downloaded files between runs, keyed by the lock file's hash. Runs on `main` save it; pull requests and the merge queue only read it, and every file taken from it is checked like a download. Between two changes of the lock, runs then need no Ubuntu server at all.

No rule of ADR-0017 is loosened. The base is pinned by digest and at least a day old; every file is pinned by SHA-256 in the repository and older than the session's cutoff, because it was in the archive at a snapshot date before the cutoff; nothing is chosen at run time, by apt or by anyone else. The [amendment of 2026-11-05 to ADR-0017](../../adr/0017-supply-chain-and-dependency-policy.md#amendment-2026-11-05-ubuntu-packages-in-ci), proposed together with this brief, records the decision. It keeps every rule at least as strict, so the orchestrator decides it ([plan/12](../../plan/12-orchestration.md#what-only-the-owner-decides)), and this work package starts once it is accepted.

### What was measured

This planning session measured the design on 2026-11-05 with Docker in the BayanDocs cloud environment, where downloads go through the session's network proxy, which is slower than GitHub's network:

| | bayan-desktop | bayan-web |
|---|---|---|
| Requested packages | the six -dev packages, plus python3-venv, g++, xz-utils, zstd and rustup, which the runner image provided until now | the 79 browser libraries, plus unzip and xz-utils |
| Lock on `buildpack-deps:noble-scm` (created 2026-10-26) at the snapshot of 2026-10-27 | 123 files, 138.5 MB | 366 files, 218.6 MB |
| Downloading the files one after another, each checked | 113 s | 423 s |
| Installing them in a container without network, in apt's recorded order | 11.4 s (2 dpkg calls) | 28.6 s (4 dpkg calls) |
| Disk used, base image included | 917 MB | 1214 MB |

- **The order matters.** One `dpkg -i` call with all files is not enough: it configures packages only at the end, and `systemd-sysv` must not be unpacked before `systemd` is configured (a pre-dependency), so the web set fails. `apt-get install ./*.deb` without a package index stops with `E: Internal Error, Pathname to install is not absolute`. Replaying apt's own plan (the `Inst` and `Conf` lines of `apt-get -s install`) as batched `dpkg --unpack` and `dpkg --configure` calls installs both sets with `dpkg --audit` reporting nothing; gcc 13.3, Python's venv and rustup 1.26 then work.
- **The sources.** Of the 483 package files of both sets at the snapshot of 2026-10-27, all are on Launchpad, and all but 2 (libsoup 3.4.4-5ubuntu0.9) are still in the live archive nine days later. For a lock one month old (the same packages at the snapshot of 2026-10-03), 36 files had changed by 2026-10-27 and 27 are no longer on archive.ubuntu.com, but all 483 are on Launchpad and on the snapshot. The live archive is therefore only a last resort, and Launchpad is the real second source.
- **The base.** `buildpack-deps:noble-scm` (digest `sha256:94ed690dd634b8b2f531eaa742fde9b1264077cd8ea695a3b960bd104ae4c481`, created 2026-10-26 at 23:50 UTC, tag last updated 2026-11-03) is 89 MB compressed and 262 MB on disk. It is built on the same Ubuntu image (serial 20261024.1) as `ubuntu:24.04` (digest `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`, created 2026-10-25, 30 MB compressed), which has no ca-certificates, curl or git. mirror.gcr.io serves the same digest.
- **A prebuilt image** with the packages already installed would be about 250 MB (bayan-desktop) and 340 MB (bayan-web) compressed, measured on `ubuntu:24.04` with apt (724 MB and 908 MB on disk).

### What else was weighed

- **Option A alone** (a container, with the packages from the snapshot through apt): it removes skew but not outages, and each job would also download its compilers and tools from the snapshot. It is part 1 of the design.
- **A prebuilt image** with the packages installed, built from the pinned base, the snapshot and the package list, and pinned by digest: no Ubuntu server at run time at all. A workflow in each repository would build it and store it in GitHub's container registry (`ghcr.io/bayandocs/…`), with GitHub's artifact attestations to show its provenance, which the session that records the digest checks with `gh attestation verify`. But publishing a package and its registry settings are the owner's ([plan/12](../../plan/12-orchestration.md#what-only-the-owner-decides)); the job that builds the image runs the packages' maintainer scripts (the programs a package runs while it is installed), so under the [workflow conventions](../../AGENTS.md#workflow-conventions) it may not hold `packages: write`, and the job that pushes the image would have to run the docker program or a third-party action instead of only GitHub's own actions, which needs the owner too. The image also cannot be rebuilt byte for byte, so a reviewer could check it only through the attestation, while a lock file is a list that anyone can read in a diff. With the cache, the design gets most of the benefit without any of this. Not recommended now; it remains the way forward if downloads ever become the bottleneck.
- **Option B** (keep the frozen date, and fail with a clear message when the runner image is newer): the failure becomes easier to understand but not rarer. It is used only where nothing can be pinned (below).
- **Option C** (take the snapshot date from the runner image at run time): GitHub's image would choose the versions, and the repository would no longer record them, which loosens ADR-0017 and is the owner's decision. The design does not need it.
- **Exact files on the bare runner, without a container:** the -dev packages would still require the old library versions that the newer runner image has replaced, so skew would remain.
- **GitHub's custom runner images** (a pinned virtual machine image of our own): available only for larger runners, which cost money and need organization settings, so the owner's; not needed.
- **Microsoft's Playwright container image** for bayan-web: a third-party build whose browsers and Node.js our pins do not check, and no help for bayan-desktop or the agent environment.
- **Unpacking the -dev packages into a private folder** for the compiler, next to the runner's own libraries: dpkg would check nothing, so no skew, but the build set-up would be unusual and differ from developers' machines.

### Where the current method stays

- **Developers' own Ubuntu machines** (bayan-web's `scripts/dev-setup.sh` outside CI) and **the agent environment** (`scripts/cloud-environment-setup.sh`) keep installing from the signed archive frozen at a snapshot date. Their base belongs to the developer or to the cloud environment, not to the project, and changes without notice, so it can be neither pinned nor locked against in advance. A failure there blocks no pull request: dev-setup stops with apt's message, and the agent environment's setup never blocks a session, lists a failed step in `bayandocs-tools`, and keeps its result for about seven days. The agent environment gets two small changes through [issue #7](https://github.com/BayanDocs/docs/issues/7), the batch of setup-script changes that the docs monthly session applies: the rule for its date (on or after the newest package of its image) and option B's message (see the scope).
- **macOS and Windows jobs** install no Ubuntu packages; neither do bayan-web's engine job and the workflows of bayan-core and bayan-server.

## Objective

In bayan-desktop and bayan-web, no Linux CI job depends on the runner image's libraries, or on one Ubuntu server being up, to install its Ubuntu packages: each runs in a container from a base image pinned by digest and installs exactly the files its repository's lock lists, checked against their sizes and SHA-256 hashes, from the cache, the snapshot, Launchpad or the live archive. The monthly session moves the base image, the snapshot date and the locks together.

## Scope

### In scope

- **Container jobs.** In bayan-desktop, the jobs `linux` and `sanitizers` of `ci.yml` and `cpp-analysis` of `codeql.yml`; in bayan-web, the `ubuntu-24.04` entry of the `verify` matrix of `ci.yml` (the macOS entries stay as they are). Each runs in a container from the same `buildpack-deps:noble-scm` digest, with the image's creation date in a comment. The jobs keep their names, so the required checks stay the same. Container options are added only where a job needs them (for example more shared memory for the browsers, or `--cap-add=SYS_PTRACE` if LeakSanitizer needs it), never `--privileged`. If a simpler base keeps every rule (for example `ubuntu:24.04` with a hash-checked bootstrap of ca-certificates and git), the implementer may use it and says why.
- **The lock**, one per repository (for example `deps/ubuntu-packages.lock`). A header names the base image (reference and digest) and its creation time, the snapshot date and the requested packages. Then follows apt's plan for that base and date, one step per line: each file to unpack, with its pool path, size and SHA-256, and each package to configure. The requested packages are those the jobs use: today's `UBUNTU_PACKAGES` and `APT_PACKAGES`, plus what the jobs took from the runner image until now (compilers, Python's venv, rustup, zstd, which the CodeQL action needs to unpack its bundle, xz-utils, unzip and whatever else the jobs turn out to need), each listed explicitly, installed with `--no-install-recommends`.
- **One script, identical in both repositories** (for example `scripts/ubuntu-packages.sh`, POSIX shell, clean under ShellCheck), with two commands:
  - `lock`, for the monthly session: runs apt in the pinned base image with Docker against the snapshot date (`apt-get update --snapshot`, apt's simulated install, and the sizes and SHA-256 hashes from the snapshot's index), refuses a date earlier than the image's creation or later than a cutoff it is given, and writes the lock so that the same inputs always give the same file, byte for byte;
  - `install`, for CI: for each file, takes it from the cache folder if its size and SHA-256 match, and otherwise downloads it from `https://snapshot.ubuntu.com/ubuntu/<date>/<pool path>`, then `https://launchpad.net/ubuntu/+archive/primary/+files/<file name>`, then `https://archive.ubuntu.com/ubuntu/<pool path>`. It uses HTTPS only, redirects included; goes to the next source only after a failed download, never after a size or SHA-256 mismatch, which stops the job and names the file; moves a file into place only after its check; and may download several files at a time. Then it replays the plan with dpkg (a run of unpack lines as one `dpkg --unpack` call, a run of configure lines as one `dpkg --configure` call), without apt and without network, and checks that `dpkg --audit` reports nothing and that every locked package is installed at its locked version. It ends with a summary: how many files came from the cache and from each source, and the time taken.
- **The cache.** `actions/cache/restore` before the install and `actions/cache/save` right after it, at the commit that bayan-core's fuzzing workflow already pins (`55cc8345863c7cc4c66a329aec7e433d2d1c52a9`, v6.1.0), so no new action pin is needed; the key is derived from the lock's hash; only runs on `main` (pushes and scheduled runs) save, never a pull request or the merge queue.
- **Tests**, in each repository's gate and test framework (bayan-desktop: Python run by CTest, like `tests/install-qt`; bayan-web: vitest, like `tests/unit/engine-pin.test.ts`):
  - the lock is well formed, its snapshot date is on or after its base image's creation, every unpacked package is configured, and every job that installs it uses the base image of its header (this replaces `tests/workflows/test_ubuntu_packages.py`);
  - the installer, against a local server: a failed download moves to the next source; a size or SHA-256 mismatch stops without trying another source; a redirect to an address that is not HTTPS is refused; a cached file is checked, and a bad one stops the job;
  - the `lock` command refuses a snapshot date before the image's creation or after the cutoff.
- **bayan-web's `scripts/dev-setup.sh`** stays unchanged for machines outside the container. In the container, the installer has already installed every package of `APT_PACKAGES`, so the script's library step reports them installed and calls no apt; it runs as root without sudo (its `as_root` already allows that). `APT_SNAPSHOT` takes the lock's snapshot date.
- **The first lock** of each repository uses the newest base image and a snapshot date chosen by the new rules, both older than the cutoff, and the same in both repositories. This moves bayan-desktop's and bayan-web's pins outside the monthly session, which the orchestrator allows when every rule of ADR-0017 holds (as for bayan-desktop#9); the pull requests state both dates.
- **Documentation**, in the same pull requests (AGENTS.md §5: a change of the dependency posture updates its documents in the same pull request):
  - the [dependency update runbook](../../developer/dependency-update-runbook.md), as described in [The runbook after this work package](#the-runbook-after-this-work-package);
  - docs `AGENTS.md` §6 (in "Tools": Ubuntu packages come from the repository's lock, installed on a base image pinned by digest), the CI bullet of bayan-desktop's `AGENTS.md` (it describes `UBUNTU_SNAPSHOT` today), the dependency section of bayan-web's `AGENTS.md`, and the header comments of the changed workflows;
  - the amendment's status line in ADR-0017 and its entry in the [ADR index](../../adr/README.md), if they do not already say that the orchestrator accepted it.
- **The agent environment:** an entry in [issue #7](https://github.com/BayanDocs/docs/issues/7), in that issue's format, for `scripts/cloud-environment-setup.sh`: (1) `APT_SNAPSHOT` is the locks' snapshot date, and on or after the newest Ubuntu package of the environment's image (`/var/log/dpkg.log` in a session shows it); (2) when the apt step fails, its note says whether the snapshot could not be reached or the image has newer libraries than the date (apt's "unmet dependencies" on a newer installed version), and what to do in each case; (3) one retry after a short pause when the snapshot could not be reached, within the script's time limit.

### Out of scope

- Option C, a published prebuilt image, GitHub's custom runner images (each needs the owner), and downgrading libraries.
- The monthly sessions' later moves of these pins, and every other pin (Node.js, pnpm, Qt, the browsers, the actions).
- Changing `scripts/cloud-environment-setup.sh` itself (the docs monthly session applies the issue #7 batch), developers' machines beyond what is written above, and the macOS and Windows jobs.
- Scanning the locked packages for known vulnerabilities (for example with grype, which can read a container image): a follow-up.
- The other follow-ups of X-004.

## The runbook after this work package

The rows of the [dependency update runbook](../../developer/dependency-update-runbook.md) that change, with what they should say:

| Section and row | New content |
|---|---|
| bayan-desktop, "Ubuntu packages" | Where: the base image of the Linux jobs (`container:` in `ci.yml` and in the C++ analysis job of `codeql.yml`) and the lock, whose header holds the snapshot date and the requested packages; bayan-web pins the same base image and date. How: (1) take the newest digest of `buildpack-deps:noble-scm` whose `last_updated` on Docker Hub is before the cutoff, and write it, with the image's creation time, in every job; (2) choose a snapshot date before the cutoff and on or after the image's creation, usually the day before the session at 00:00 UTC; (3) regenerate the lock with the script's `lock` command (Docker, see "Before you start"), review its diff, run the gate, and let CI install the new lock. A package that apt adds as a dependency of a requested one needs no justification; a newly requested package does (AGENTS.md §5). The tests keep the jobs' base image equal to the lock's. |
| bayan-desktop, "Python in CI" | The Linux jobs use the container's Python 3 (Ubuntu 24.04's, from the base image or the lock); the macOS and Windows jobs keep the runner image's own. |
| bayan-web, "Ubuntu packages (the browsers' libraries)" | As for bayan-desktop, with the same base image and snapshot date; `APT_SNAPSHOT` in `scripts/dev-setup.sh` takes the same date, for developers' machines. |
| docs, "Agent environment" | `APT_SNAPSHOT`: the locks' snapshot date, and on or after the newest Ubuntu package of the environment's image (`/var/log/dpkg.log` in the session); if that package is newer than the cutoff, take the cutoff and say so in the pull request. Running the script in the session shows whether the apt step works. |
| Finding publish dates, "Ubuntu packages" | The snapshot date of the locks and of `APT_SNAPSHOT`: before the cutoff, and on or after the creation time of the CI base image; every file in Ubuntu's archive at that moment was published before it. |
| Finding publish dates, "Container image" | Also names `buildpack-deps:noble-scm`, the base of the Linux CI jobs of bayan-desktop and bayan-web. |
| How the rules are enforced, bayan-desktop and bayan-web | Checked automatically: the installer checks every Ubuntu package file against the lock's size and SHA-256; a test keeps the jobs' base image equal to the lock's, and the lock's snapshot date on or after the image's creation. Your job: check the base image's date by hand. |
| Before you start | Docker for the `lock` command: in a cloud session the daemon is not running; start it (`nohup dockerd >/tmp/dockerd.log 2>&1 &`). |

## Deliverables

- **bayan-desktop:** `ci.yml` and `codeql.yml` with container jobs, the lock, the script and its tests (without `tests/workflows/test_ubuntu_packages.py`), and `AGENTS.md`.
- **bayan-web:** `ci.yml` with the container entry, the lock, the same script and its tests, `scripts/dev-setup.sh` (`APT_SNAPSHOT`) and `AGENTS.md`.
- **docs:** the runbook rows, `AGENTS.md` §6 and, if needed, the amendment's status; the issue #7 entry.

## Acceptance criteria

- [ ] AC-1 In both repositories, every Linux job that installs Ubuntu packages runs in a container from the same base image pinned by digest, and no workflow step runs apt or names a snapshot date (the diffs, and a `git grep` of `.github/` that finds `apt-get` and `--snapshot` in no `run:` step).
- [ ] AC-2 Each lock states its base image's digest and creation time, its snapshot date and its requested packages, and the script's `lock` command reproduces it byte for byte from those inputs (the command and an empty `git diff` in the pull request).
- [ ] AC-3 The installer's tests show: a failed download moves to the next source; a size or SHA-256 mismatch stops without trying another source; a redirect to an address that is not HTTPS is refused; a cached file is checked, and a bad one stops the job (test names, passing in each gate).
- [ ] AC-4 The lock's test and the `lock` command's date checks pass in each gate, and fail when a job's base image differs from the lock's or the snapshot date is earlier than the image's creation (test names).
- [ ] AC-5 On a test branch where the snapshot's address is replaced by one that cannot answer, the container jobs of both repositories pass, their install summaries showing the files taken from Launchpad (links to the runs).
- [ ] AC-6 On a test branch with one wrong SHA-256 in a lock, the install step fails, names that file and tries no other source for it (link to the run).
- [ ] AC-7 On a test branch whose workflow also saves the cache (there only), a second run restores it and downloads nothing (links to both runs).
- [ ] AC-8 On the pull requests every check passes, the required checks under unchanged names: bayan-desktop's verification gate, sanitizers and engine SDK steps in the container, and its C++ analysis with its results in code scanning under `/language:c-cpp`; bayan-web's `pnpm verify (ubuntu-24.04)` in the container; the macOS and Windows jobs as before (links).
- [ ] AC-9 The workflow lint passes: zizmor reports nothing, and `pinact run --check --verify-min-age --min-age 1` passes (links).
- [ ] AC-10 The pull requests give the install step's time in the containers, with and without the cache, next to today's medians (59 s, 92 s and 158 s above), and compare WEB-002's measurements before and after the move into the container.
- [ ] AC-11 The runbook rows, the `AGENTS.md` sections and the issue #7 entry of the scope are written (the docs pull request and a link to the entry).

## Verification

- bayan-desktop: `. ~/.local/share/bayandocs/desktop-tools/env.sh`, then `cmake --workflow --preset verify` (it runs the new tests through CTest), and the pull request's CI.
- bayan-web: `scripts/dev-setup.sh`, then `pnpm verify`, and the pull request's CI.
- docs: `scripts/verify.sh`.
- Both code repositories: the script's `lock` command reproducing the committed lock, ShellCheck on the script, `zizmor --offline --no-config --no-ignores --collect=all --strict-collection .` in a cloud session (whose proxy refuses zizmor's online requests, which CI makes), and the test-branch runs of AC-5 to AC-7. To iterate on a job before pushing, run the base image locally with the lock installed, as this brief's measurements did.

## Notes and pitfalls

- **Docker in a cloud session.** The Docker client is installed but its daemon is not running: start it in the background (`nohup dockerd >/tmp/dockerd.log 2>&1 &`). A container reaches the network only through the session's proxy: run it with `--network host`, give apt the proxy (`Acquire::https::Proxy` set to `$HTTPS_PROXY`) and its certificate bundle (`Acquire::https::CaInfo "/root/.ccr/ca-bundle.crt"`, mounted into the container), and the same to curl. The proxy's port can change when the session restarts.
- **apt's names and indexes.** `apt-get --print-uris` URL-encodes parts of file names (an epoch as `1%3a`, `+` as `%2b`, `~` as `%7e`); take paths from the index's `Filename` field. Launchpad's `+files` address takes the pool's file name, which has no epoch. `apt-cache` shows a snapshot's versions only with `-o APT::Snapshot=<date>`; without it, it showed newer versions, without a warning (measured).
- **Order.** Record apt's simulated plan (`apt-get -s install`, its `Inst` and `Conf` lines). One `dpkg -i` with all files fails on pre-dependencies, and `apt-get install ./*.deb` without an index stops with an internal error (both measured, see above).
- **Inside the container.** GitHub mounts the workspace, and the runner's Node.js for JavaScript actions, into the container, and steps run as root without sudo. git refuses to work in a repository that another user owns ("dubious ownership"), so steps that run git after the checkout may need `git config --global --add safe.directory "$GITHUB_WORKSPACE"`. Browsers need more shared memory than Docker's default of 64 MB (`--shm-size`, or `--ipc=host`), and Playwright's documentation also recommends `--init`. The CodeQL action unpacks its `.tar.zst` bundle with tar and zstd, and GitHub's documentation lists what code scanning needs in a container. Ubuntu's `rustup` package puts `rustup` and its `cargo` and `rustc` proxies in `/usr/bin` (checked: version 1.26.0); check that `scripts/build-engine-sdk.sh` then installs and uses the Rust version that bayan-core pins, as it does on the runner.
- **WEB-002's measurements** (keystroke latency, frame times, round trips, memory) may shift in a container; compare them before and after (AC-10).
- **Docker Hub** serves the base image before any step runs, so there is no fallback for it inside the job; bayan-server's CI already depends on Docker Hub for PostgreSQL. If pulls fail or are rate-limited, escalate (mirror.gcr.io serves the same digest).
- **Download volume.** Without the cache, a job downloads about 140 MB (bayan-desktop) or 220 MB (bayan-web). GitHub's cache holds up to 10 GB per repository.
- **One work package, three pull requests.** The script must be identical in both code repositories, so one session writes it once; most of the work is in bayan-desktop (three jobs, among them the C++ analysis and the sanitizers), less in bayan-web, and the docs pull request carries the runbook rows. Size M, at its upper end.
- **Scheduling.** This work package should be merged before the monthly dependency sessions of bayan-desktop and bayan-web (the first round is due from 2026-11-13), so that they move the new pins with the new runbook rows; the sessions of bayan-core, bayan-server and docs do not depend on it. If it is not merged by then, the orchestrator runs those three first and holds the other two, as plan/12 already holds a repository's session while another implementation session works in it.

## Escalate if

- A job cannot run in a container without `--privileged` or a capability other than those named above, or CodeQL cannot analyse the C++ build there.
- Docker Hub pulls fail or are rate-limited in CI, or Launchpad or archive.ubuntu.com refuse GitHub's runners.
- A required check's name has to change (the rulesets are the owner's).
- A lock cannot be reproduced byte for byte, or apt's plan does not install cleanly on the pinned base.
- Any part would need a third-party action, a registry, a published image or a looser rule.
