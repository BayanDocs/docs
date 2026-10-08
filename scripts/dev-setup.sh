#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Installs the tools that scripts/verify.sh needs (mdBook, lychee and typos) at their pinned versions, checking every download against its SHA-256 hash. CI runs it before scripts/verify.sh, and you can run it on your own Linux x86-64 machine. BayanDocs cloud sessions already have these tools from scripts/cloud-environment-setup.sh, so there it only confirms the versions and installs nothing.
#
# The pins live in one place: scripts/cloud-environment-setup.sh, which changes only in the monthly dependency session (ADR-0017). This script reads the versions, download addresses and hashes from it, so cloud sessions, CI and local machines always run the same tools.
#
# Usage:
#   scripts/dev-setup.sh               install any missing tool into .tools/bin inside this repository (ignored by Git)
#   scripts/dev-setup.sh --check       only check that the pinned versions are available; change nothing
#   scripts/dev-setup.sh --pip-audit   install only pip-audit, which the supply-chain check .github/supply-chain/audit_python_tools.py runs (work package X-003), into ~/.local/share/bayandocs/pip-audit-<hash of its pins> and link it as ~/.local/bin/pip-audit. Its pins are .github/supply-chain/pip-audit-requirements.txt (exact versions with SHA-256 hashes, the same file in every BayanDocs repository), installed with pip --require-hashes as wheels only, on Linux x86-64.
# Running it again is safe: a tool already present at its pinned version is left alone.
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
pins="$repo/scripts/cloud-environment-setup.sh"
bin_dir="$repo/.tools/bin"
export PATH="$bin_dir:$PATH"

mode=install
case "${1:-}" in
  "") ;;
  --check) mode=check ;;
  --pip-audit) mode=pip-audit ;;
  *) echo "usage: scripts/dev-setup.sh [--check | --pip-audit]" >&2; exit 2 ;;
esac

# pip-audit lives in a virtual environment named after a hash of its pin file, so that a changed pin always gets a fresh environment and an unchanged one is reused.
if [[ $mode == pip-audit ]]; then
  if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    echo "error: the pinned pip-audit wheels are for Linux x86-64; elsewhere, install the versions in .github/supply-chain/pip-audit-requirements.txt yourself." >&2
    exit 1
  fi
  requirements="$repo/.github/supply-chain/pip-audit-requirements.txt"
  venv="${XDG_DATA_HOME:-$HOME/.local/share}/bayandocs/pip-audit-$(sha256sum "$requirements" | cut -c1-12)"
  link_dir="$HOME/.local/bin"
  if [[ ! -x $venv/bin/pip-audit ]]; then
    rm -rf -- "$venv"
    python3 -m venv "$venv"
    "$venv/bin/pip" install --quiet --no-input --disable-pip-version-check --require-hashes --only-binary :all: --requirement "$requirements"
  fi
  mkdir -p "$link_dir"
  ln -sfn "$venv/bin/pip-audit" "$link_dir/pip-audit"
  echo "ok       $("$venv/bin/pip-audit" --version) ($link_dir/pip-audit)"
  case ":$PATH:" in
    *":$link_dir:"*) ;;
    *) echo "note: add $link_dir to your PATH, or run $venv/bin/pip-audit" ;;
  esac
  exit 0
fi

# Prints the pin of a release binary from the BINARIES list in the cloud setup script as "version url sha256 member", where member is the path of the binary inside the archive.
binary_pin() {
  local line name version url sha256 member
  line=$(grep -E "^[[:space:]]*\"$1 " "$pins") || { echo "error: no pin for $1 in $pins" >&2; return 1; }
  line=${line#*\"}
  line=${line%\"*}
  # The fields of a BINARIES entry: name, version, URL, SHA-256, path inside the archive, source to build from.
  read -r name version url sha256 member _ <<<"$line"
  echo "$version $url $sha256 $member"
}

# Reads the typos pin (version and the SHA-256 of its manylinux x86-64 wheel) from the hash-pinned requirements in the cloud setup script.
typos_pin() {
  local block
  block=$(sed -n '/^req_typos()/,/^}/p' "$pins")
  typos_version=$(sed -n 's/^typos==\([^ ]*\).*/\1/p' <<<"$block")
  typos_sha256=$(sed -n 's/.*--hash=sha256:\([0-9a-f]\{64\}\).*/\1/p' <<<"$block" | head -n 1)
  [[ -n $typos_version && -n $typos_sha256 ]] || { echo "error: no typos pin in $pins" >&2; return 1; }
}

pin=$(binary_pin mdbook)
read -r mdbook_version mdbook_url mdbook_sha256 mdbook_member <<<"$pin"
pin=$(binary_pin lychee)
read -r lychee_version lychee_url lychee_sha256 lychee_member <<<"$pin"
typos_pin
typos_url="https://files.pythonhosted.org/packages/py3/t/typos/typos-${typos_version}-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"

# True if the command on PATH reports the pinned version (for example "mdbook v0.5.4", "lychee 0.24.2", "typos-cli 1.50.3").
has_version() {
  local found
  command -v "$1" >/dev/null 2>&1 || return 1
  found=$("$1" --version 2>/dev/null | head -n 1) || return 1
  found=${found##* }
  [[ ${found#v} == "$2" ]]
}

# Downloads a URL over HTTPS and checks its SHA-256 before anything uses it.
fetch() {
  local url=$1 sha256=$2 out=$3
  curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location --retry 3 --output "$out" "$url"
  if ! echo "$sha256  $out" | sha256sum --check --quiet --strict -; then
    echo "error: $url does not match its pinned SHA-256 hash; refusing to install it" >&2
    return 1
  fi
}

install_from_tarball() {
  local name=$1 url=$2 sha256=$3 member=$4 tmp
  tmp=$(mktemp -d)
  fetch "$url" "$sha256" "$tmp/archive.tar.gz" || { rm -rf -- "$tmp"; return 1; }
  tar -xzf "$tmp/archive.tar.gz" -C "$tmp" --no-same-owner "$member"
  install -D -m 0755 "$tmp/$member" "$bin_dir/$name"
  rm -rf -- "$tmp"
}

# A wheel is a zip archive; the typos binary is at typos-<version>.data/scripts/typos inside it.
install_typos() {
  local tmp
  tmp=$(mktemp -d)
  fetch "$typos_url" "$typos_sha256" "$tmp/typos.whl" || { rm -rf -- "$tmp"; return 1; }
  python3 - "$tmp/typos.whl" "typos-$typos_version.data/scripts/typos" "$tmp/typos" <<'EOF'
import shutil, sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as wheel, wheel.open(sys.argv[2]) as source, open(sys.argv[3], "wb") as target:
    shutil.copyfileobj(source, target)
EOF
  install -D -m 0755 "$tmp/typos" "$bin_dir/typos"
  rm -rf -- "$tmp"
}

missing=()
for tool in mdbook lychee typos; do
  version_var="${tool}_version"
  if has_version "$tool" "${!version_var}"; then
    echo "ok       $tool ${!version_var} ($(command -v "$tool"))"
  else
    missing+=("$tool")
  fi
done
[[ ${#missing[@]} -eq 0 ]] && exit 0

if [[ $mode == check ]]; then
  for tool in "${missing[@]}"; do
    version_var="${tool}_version"
    echo "missing  $tool ${!version_var}" >&2
  done
  echo "Run scripts/dev-setup.sh to install the pinned versions." >&2
  exit 1
fi

if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
  echo "error: this script installs tools on Linux x86-64 only. Install these exact versions yourself: ${missing[*]} (mdbook $mdbook_version, lychee $lychee_version, typos $typos_version)." >&2
  exit 1
fi

for tool in "${missing[@]}"; do
  case $tool in
    mdbook) install_from_tarball mdbook "$mdbook_url" "$mdbook_sha256" "$mdbook_member" ;;
    lychee) install_from_tarball lychee "$lychee_url" "$lychee_sha256" "$lychee_member" ;;
    typos) install_typos ;;
  esac
  version_var="${tool}_version"
  has_version "$tool" "${!version_var}" || { echo "error: $tool ${!version_var} did not install correctly" >&2; exit 1; }
  echo "installed $tool ${!version_var} ($bin_dir/$tool)"
done
