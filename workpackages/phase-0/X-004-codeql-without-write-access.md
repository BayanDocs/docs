# X-004: CodeQL without write access — analysis and upload in separate jobs

| Field | Value |
|---|---|
| Phase | 0 — Bedrock |
| Stream | SECURITY |
| Repository | all five |
| Attach to session | all five repositories |
| Size | S |
| Depends on | X-002 |
| Unblocks | The first monthly dependency session's move of the CodeQL bundle ([plan/12 §7](../../plan/12-orchestration.md#7-specialty-sessions)) |
| Status | Ready |
| Requirements | SEC-05, SEC-12 |
| Decisions | ADR-0017 (amendment of 2026-10-10, CodeQL), ADR-0025 |
| Specs | [threat-model.md §11](../../specs/threat-model.md#11-principal-threats) (T16) |

## Context

X-002 added CodeQL, GitHub's static analysis, to every repository as `.github/workflows/codeql.yml`. In each, the jobs that analyse the code also upload the results to GitHub's code scanning, so they hold the permission `security-events: write` next to `contents: read`. That permission lets a job upload results and change the state of code-scanning alerts, for example dismiss them. Any program that runs in a job can get hold of the job's token (on GitHub's runners, a step can even read it from the memory of the runner's process), so a job that runs code it does not control should hold no write permission. The reviews of X-002's pull requests (bayan-core#15, bayan-server#6, bayan-desktop#5 and docs#30) raised this; nothing changed since. At today's `main` branches (bayan-core `3c5a18f`, bayan-desktop `b9b217a`, bayan-web `01c5978`, bayan-server `835034a`, docs `be86598`):

- **The build-less jobs** (`analyze`, a matrix over `actions`, `python`, `javascript-typescript` and, in bayan-core, `c-cpp` without a build) run only the CodeQL action on the checked-out files.
- **bayan-core's and bayan-server's `rust` job** ([bayan-core codeql.yml:71](https://github.com/BayanDocs/bayan-core/blob/3c5a18f268ab677fd58bca7909673477114f4322/.github/workflows/codeql.yml#L71), [bayan-server codeql.yml:70](https://github.com/BayanDocs/bayan-server/blob/835034aeb424de6b8e160bbb3d567029bfca94d8/.github/workflows/codeql.yml#L70)) first compiles and runs the repository's own `xtask` (`cargo xtask check-exact-pins` and `check-lockfile-age`), and CodeQL's Rust extractor then runs `cargo check`, which runs the build scripts and procedural macros of the dependencies. Today that `cargo check` stops at once, because CodeQL 2.27.2's extractor installs Rust 1.98.1, older than the workspaces' `rust-version` 1.99; a later bundle will run it.
- **bayan-desktop's `cpp` job** ([codeql.yml:70](https://github.com/BayanDocs/bayan-desktop/blob/b9b217a3ab7df2b217303f0915c9eacc35a54f74/.github/workflows/codeql.yml#L70)) runs `scripts/dev-setup.sh`, the Qt installer and a CMake build of the pull request's code (`build-mode: manual`), all with the write permission.
- **The pattern already exists.** Every repository's Scorecard workflow (`.github/workflows/scorecard.yml`, identical in all five) splits its work this way: an analysis job with read permissions keeps its SARIF file (the results format of code scanning) as a workflow artifact, and an upload job, which runs no code of the repository, downloads it and uploads it with `github/codeql-action/upload-sarif`, the only job with `security-events: write`.
- **The required checks.** The settings baseline, [scripts/github-settings.py](../../scripts/github-settings.py), makes the CodeQL jobs required checks of `main` by name: `CodeQL (actions)` and `CodeQL (python)` everywhere, plus `CodeQL (javascript-typescript)`, `CodeQL (c-cpp)` and `CodeQL (rust)` where a repository has them (the owner applies the baseline; finding H1 of the architecture review found the live rules lagging behind it). GitHub reports a job that was skipped, for example because a job it `needs` failed, as passing, and a skipped required check does not block a merge.
- **The rule in AGENTS.md.** [§6](../../AGENTS.md#workflow-conventions) says that CodeQL's workflow is the same in all five repositories except for its list of languages, the paths a repository leaves out and the job of a language that needs a toolchain or a build.

**Why now.** The first monthly dependency session is due once Rust 1.100 (released 2026-11-12) is 24 hours old ([plan/12 §7](../../plan/12-orchestration.md#7-specialty-sessions)), and it will move the CodeQL bundle with the rest. A bundle whose Rust extractor accepts Rust 1.99 makes `cargo check` run dependencies' code in a job that holds the write permission.

## Objective

In every repository, no job of `codeql.yml` that runs code of the repository, of its tools or of its dependencies holds a write permission; only small upload jobs that run nothing but GitHub's own actions do, and a failed analysis or upload still fails the required check of its language.

## Scope

### In scope

- **The split, in all five repositories.** Each analysis job keeps read permissions only (`contents: read`, and a read permission such as `security-events: read` if CodeQL needs one; each with its comment), runs CodeQL's `analyze` step without uploading (its `upload` input, for example `never`, writing the SARIF file to a folder given as `output`), and keeps the SARIF file as a workflow artifact with a short retention, as Scorecard does. An upload job per language checks out the repository without credentials (as Scorecard's does, so that the upload can match results to files), downloads the artifact and uploads it with `upload-sarif`, with the same category as today (`/language:<language>`) and `security-events: write`. Apply it to the build-less languages too, so that the workflow stays the same everywhere.
- **The required checks keep their names and their meaning.** The job named `CodeQL (<language>)` must succeed only when both the analysis and the upload succeeded, and must never be skipped: for example, name the upload job `CodeQL (<language>)`, run it with `if: ${{ !cancelled() }}`, and make its first step fail unless its analysis job succeeded; name the analysis job `CodeQL analysis (<language>)`. With a matrix, make sure each language's upload job judges its own analysis, not the matrix as a whole. If keeping the names turns out to be impossible, change `scripts/github-settings.py` in the docs pull request and tell the orchestrator that the owner must apply the settings, which only the owner can do.
- **Pins.** `actions/upload-artifact`, `actions/download-artifact` and `github/codeql-action/upload-sarif` at the commits the repositories already pin (Scorecard's workflow uses all three), so that no new pin is needed; any new pin must be at least 24 hours old.
- **Documentation.** A workflow convention in docs `AGENTS.md` §6 and in each repository's `AGENTS.md` ("Workflow conventions"): a job that runs code of the repository, its tools or its dependencies never holds a write permission; results it produces go to a separate job that runs only GitHub's own actions. Update the comment at the top of each `codeql.yml` and the "Shared workflows" item of §6 if its wording no longer fits. In docs, also update the `codeql.yml` row of the [dependency update runbook](../../developer/dependency-update-runbook.md): it tells the monthly session to split these jobs, or to ask the owner to accept the risk, before taking a bundle whose Rust extractor runs `cargo check`, which this work package makes obsolete (AGENTS.md §5: a document about the dependency posture changes in the same pull request as the posture).

### Out of scope

- The CodeQL bundle's version and the languages scanned (the monthly dependency session).
- Repository settings and rulesets (the owner).
- The other workflows; a job elsewhere that holds a write permission and runs code becomes a follow-up.

## Deliverables

One pull request per repository: the five `codeql.yml` files, the code repositories' `AGENTS.md`, and in docs also `AGENTS.md` §6 and the runbook's `codeql.yml` row (and `scripts/github-settings.py` only if a check's name must change).

## Acceptance criteria

- [ ] AC-1 In each repository's `codeql.yml`, `security-events: write` appears only in upload jobs whose steps are `actions/checkout` (without credentials), `actions/download-artifact` and `github/codeql-action/upload-sarif`, and no job that installs or runs anything else holds a write permission (the diff of each workflow, and zizmor's clean report).
- [ ] AC-2 On a test branch, a failing analysis (for example a build that fails on purpose) and a failing upload (for example a SARIF file removed before the upload) each make `CodeQL (<language>)` fail, not skip (links to both runs).
- [ ] AC-3 On each pull request, the CodeQL runs pass and their results appear in code scanning under the same categories as before (links).
- [ ] AC-4 The workflow lint passes in every repository (`zizmor` with no findings, `pinact run --check --verify-min-age --min-age 1`).
- [ ] AC-5 The parts of `codeql.yml` that AGENTS.md §6 says are shared are identical in all five repositories (a diff in the pull request).
- [ ] AC-6 The runbook's `codeql.yml` row no longer asks the monthly session to split the jobs or to ask the owner, and says what the split guarantees instead.

## Verification

In each repository its verification gate (`cargo xtask verify`, `cmake --workflow --preset verify`, `pnpm verify`, the server's gate, and `scripts/verify.sh` in docs), `zizmor --offline --no-config --no-ignores --collect=all --strict-collection .` in a cloud session (whose proxy refuses zizmor's online requests, which CI makes), the CI runs of each pull request, and the test-branch runs of AC-2.

## Notes and pitfalls

- **Scheduling.** The five pull requests should be merged before the first monthly dependency session moves the CodeQL bundle, which is due once Rust 1.100 is 24 hours old (from 2026-11-13).
- **Check early what CodeQL needs.** What `codeql init` and `analyze` do without `security-events: write` was left open by docs#30's follow-up 3; find out first, in CI, on a test branch. A read permission such as `security-events: read` fits the objective; a write permission does not.
- **The artifact is public.** Anyone signed in to GitHub can download a public repository's artifacts, and a SARIF file holds every result of the analysis, not only new ones. Every input of the analysis is public too: the code, the queries and the bundle's pinned version, so anyone can compute the same results with CodeQL, which GitHub offers for free for open-source code. Keep the retention short (one day is enough for a run), and do not put anything else into the artifact.
- **Pull requests from forks** get a read-only token, so their upload fails as it does today; nothing changes for them.
- **`merge_group`.** The rulesets' merge queue waits for the required checks on its own commit, so the upload job must run there too, with the same name.
- The Rust and C++ jobs keep their supply-chain checks before anything of the dependencies is fetched or built.

## Escalate if

- The upload needs a permission or an action that GitHub's own actions cannot provide, or a third-party action.
- A required check's name cannot stay the same.
- CodeQL refuses to upload a SARIF file produced in another job of the same run (for example because of how it identifies the analysis).
