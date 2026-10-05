#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# The verification gate of the BayanDocs knowledge base (AGENTS.md §10, work package DOCS-001). Run it before every push. CI runs it on every pull request and every push to main, and the website is deployed only from a commit that passes it.
#
# What it checks, in order:
#   1. the pinned tools are installed (scripts/dev-setup.sh --check);
#   2. every Markdown page is in the website's navigation, SUMMARY.md (apart from the few files listed in NOT_PAGES below);
#   3. every ADR and work package ID mentioned in the Markdown exists;
#   4. the vendored Mermaid script matches its recorded checksums (site/mermaid/README.md);
#   5. the website builds with mdBook, from a copy of only the files Git tracks, into book/;
#   6. every link between files works, including its #anchor, both in the Markdown (as GitHub shows it) and in the built website (lychee, offline);
#   7. every external link works (lychee, online, results cached for a day; skipped with --offline);
#   8. there are no known misspellings (typos, with the project dictionary in typos.toml);
#   9. the unit tests of the scripts pass (scripts/tests/, Python's unittest).
# Every check runs even when an earlier one fails (except that missing tools or a failed build stop the run), and a summary at the end lists what failed.
#
# Usage: scripts/verify.sh [--offline]
#   --offline   skip only the external-link check, for machines without internet access. The pull-request check in CI always runs it.
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo"
# Prefer tools installed by scripts/dev-setup.sh.
export PATH="$repo/.tools/bin:$PATH"

offline=false
case "${1:-}" in
  "") ;;
  --offline) offline=true ;;
  *) echo "usage: scripts/verify.sh [--offline]" >&2; exit 2 ;;
esac

# Markdown files that are deliberately not pages of the website.
NOT_PAGES=(
  CLAUDE.md               # tells Claude Code to read AGENTS.md; AGENTS.md itself is in the book
  SUMMARY.md              # the website's navigation
  site/mermaid/README.md  # maintenance note for the vendored Mermaid script
)
# Work package IDs, such as CORE-001 or X-101 (workpackages/README.md).
WP_ID='(CORE|LAB|DESK|WEB|SRV|DOCS|X)-[0-9]{3}'

failures=()
# run <description> <command> [arguments]: runs one check and records it if it fails.
run() {
  local description=$1
  shift
  echo "==> $description"
  if "$@"; then
    echo "    ok"
  else
    echo "    FAILED: $description"
    failures+=("$description")
  fi
}

# The files Git tracks, plus new files not yet committed (but not ignored ones), without files deleted from the working folder.
files=()
while IFS= read -r -d '' file; do
  if [[ -L $file ]]; then
    echo "error: $file is a symbolic link; the website is built from regular files only, so that nothing outside the repository can be published" >&2
    exit 1
  fi
  if [[ -f $file ]]; then
    files+=("$file")
  fi
done < <(git ls-files -z --cached --others --exclude-standard)
markdown_files=()
for file in "${files[@]}"; do
  if [[ $file == *.md ]]; then
    markdown_files+=("$file")
  fi
done
# Markdown files whose links are checked: all except SUMMARY.md, whose entries mdBook checks itself (and whose section headings have no link).
link_sources=()
for file in "${markdown_files[@]}"; do
  if [[ $file != SUMMARY.md ]]; then
    link_sources+=("$file")
  fi
done

is_not_page() {
  local entry
  for entry in "${NOT_PAGES[@]}"; do
    if [[ $1 == "$entry" ]]; then
      return 0
    fi
  done
  return 1
}

check_tools() {
  scripts/dev-setup.sh --check
}

check_navigation() {
  local file failed=0
  for file in "${markdown_files[@]}"; do
    if is_not_page "$file"; then
      continue
    fi
    if ! grep -qF "]($file)" SUMMARY.md; then
      echo "    $file is not in SUMMARY.md (add it to the navigation, or to NOT_PAGES in scripts/verify.sh if it is not a page)"
      failed=1
    fi
  done
  return "$failed"
}

check_ids() {
  local id file failed=0 defined=()
  # ADR-NNNN must have a file adr/NNNN-<title>.md.
  while read -r id; do
    if ! compgen -G "adr/${id#ADR-}-*.md" >/dev/null; then
      echo "    $id is mentioned, but there is no adr/${id#ADR-}-*.md"
      failed=1
    fi
  done < <(grep -ohE '\bADR-[0-9]{4}\b' "${markdown_files[@]}" | sort -u)
  # A work package is defined by its brief (workpackages/phase-N/<ID>-<title>.md) or by a draft heading such as "### CORE-101 — Title" in workpackages/.
  for file in "${markdown_files[@]}"; do
    if [[ $file != workpackages/* ]]; then
      continue
    fi
    if [[ ${file##*/} =~ ^($WP_ID)- ]]; then
      defined+=("${BASH_REMATCH[1]}")
    fi
    while read -r id; do
      defined+=("$id")
    done < <(grep -oE "^#{2,4} +$WP_ID\b" "$file" | grep -oE "$WP_ID")
  done
  while read -r id; do
    if ! printf '%s\n' "${defined[@]}" | grep -qxF "$id"; then
      echo "    $id is mentioned, but no work package brief or draft defines it"
      failed=1
    fi
  done < <(grep -ohE "\b$WP_ID\b" "${markdown_files[@]}" | sort -u)
  return "$failed"
}

check_mermaid() {
  local integrity
  if ! (cd site/mermaid && sha256sum --check --strict SHA256SUMS); then
    echo "    site/mermaid/mermaid.min.js does not match site/mermaid/SHA256SUMS"
    return 1
  fi
  integrity="sha384-$(openssl dgst -sha384 -binary site/mermaid/mermaid.min.js | base64 -w 0)"
  if ! grep -qF "\"$integrity\"" site/mermaid/mermaid-init.js; then
    echo "    site/mermaid/mermaid-init.js does not contain the file's integrity hash $integrity"
    return 1
  fi
}

# mdBook copies every non-Markdown file of its source folder into the website, including hidden ones such as .git, so the website is built from a temporary copy of the tracked files only. Hidden files and folders (.github/, .gitignore) are left out.
build_site() {
  local stage file status=0
  stage=$(mktemp -d)
  for file in "${files[@]}"; do
    if [[ $file == .* || $file == */.* ]]; then
      continue
    fi
    mkdir -p "$stage/$(dirname "$file")"
    cp "$file" "$stage/$file"
  done
  rm -rf book
  mdbook build --dest-dir "$repo/book" "$stage" || status=$?
  rm -rf -- "$stage"
  return "$status"
}

check_internal_links() {
  local failed=0
  echo "    links in the Markdown files:"
  printf '%s\n' "${link_sources[@]}" | lychee --config lychee.toml --offline --include-fragments --no-progress --files-from - || failed=1
  echo "    links in the built website:"
  # The 404 page uses links relative to the address the site is served from (site-url in book.toml), which only exist once deployed.
  lychee --config lychee.toml --offline --include-fragments --index-files index.html --no-progress \
    --exclude-path '^book/404\.html$' 'book/**/*.html' || failed=1
  return "$failed"
}

check_external_links() {
  printf '%s\n' "${link_sources[@]}" | lychee --config lychee.toml --cache --scheme https --scheme http --no-progress --files-from -
}

check_spelling() {
  typos
}

check_script_tests() {
  python3 -m unittest discover --start-directory scripts/tests
}

run "Pinned tools are installed" check_tools
if [[ ${#failures[@]} -gt 0 ]]; then
  echo "Stopping: install the tools first (scripts/dev-setup.sh)." >&2
  exit 1
fi
run "Every page is in the navigation (SUMMARY.md)" check_navigation
run "Every ADR and work package ID mentioned exists" check_ids
run "The vendored Mermaid script matches its checksums" check_mermaid
run "The website builds (mdBook)" build_site
if [[ ! -f book/index.html ]]; then
  echo "Stopping: the website did not build, so its links cannot be checked." >&2
  exit 1
fi
run "Links between files and their #anchors work (Markdown and website)" check_internal_links
if $offline; then
  echo "==> External links: NOT CHECKED (--offline)"
else
  run "External links work" check_external_links
fi
run "No known misspellings (typos)" check_spelling
run "The scripts' unit tests pass (scripts/tests)" check_script_tests

echo
if [[ ${#failures[@]} -gt 0 ]]; then
  echo "scripts/verify.sh: ${#failures[@]} check(s) failed:"
  printf '  - %s\n' "${failures[@]}"
  exit 1
fi
if $offline; then
  echo "scripts/verify.sh: all checks passed (external links were not checked)."
else
  echo "scripts/verify.sh: all checks passed."
fi
