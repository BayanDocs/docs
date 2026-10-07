#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# BayanDocs cloud environment setup script, version 2026-10-07.1.
#
# Installs the tools that BayanDocs agent sessions need in a Claude Code cloud environment (Ubuntu 24.04, x86-64, run as root before Claude Code starts). Paste this whole file into the environment's settings: the cloud environment menu in the session's title bar, then Edit, then "Setup script". The result is cached for about seven days, or until this script or the network settings change. Canonical copy: https://github.com/BayanDocs/docs/blob/main/scripts/cloud-environment-setup.sh
#
# Supply-chain rules (ADR-0017): every version below is pinned exactly and was at least 24 hours old when it was pinned, and every download is verified: release archives against the SHA-256 hashes in this file, pnpm's native binary against the SHA-512 hash in this file, Python packages with `pip --require-hashes`, Qt by aqtinstall against hashes from download.qt.io, Rust toolchains by rustup against the hashes in the official release manifests, and Ubuntu packages by apt from the signed archive frozen at a snapshot date. Pins change only in the monthly dependency session (docs/plan/06-agent-workflow.md), which then asks the owner to paste the new version here.
#
# Network: everything comes from the default "Trusted" list except Qt, which needs download.qt.io and master.qt.io.
# The script never blocks a session: a failed step is reported, and the script still exits 0. Run `bayandocs-tools` in a session to see what was installed; full logs are in /var/log/bayandocs-setup/.

# The steps below are called indirectly through start(), which ShellCheck cannot follow.
# shellcheck disable=SC2317
set -uo pipefail
umask 022
export HOME="${HOME:-/root}" DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1
export PATH="/root/.cargo/bin:/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# The cloud network inspects TLS with a certificate authority that is in the system trust store. pip, Python's requests library and Node.js bring their own lists of authorities, so point them at the system store (curl, apt, rustup and Go use it).
SYSTEM_CA=/etc/ssl/certs/ca-certificates.crt
export PIP_CERT="${PIP_CERT:-$SYSTEM_CA}" REQUESTS_CA_BUNDLE="${REQUESTS_CA_BUNDLE:-$SYSTEM_CA}"
export NODE_EXTRA_CA_CERTS="${NODE_EXTRA_CA_CERTS:-$SYSTEM_CA}"

# ---------------------------------------------------------------------------------------------------------------------
# Pins. Update only in the monthly dependency session, checking each publish date (at least 24 hours old) and hash.
# ---------------------------------------------------------------------------------------------------------------------
SCRIPT_VERSION=2026-10-07.1
APT_SNAPSHOT=20261003T000000Z    # Ubuntu archive as of 2026-10-03 00:00 UTC (snapshot.ubuntu.com)
APT_PACKAGES="libgl-dev libegl-dev libvulkan-dev libxkbcommon-dev libfontconfig-dev libdbus-1-dev shellcheck"
RUST_STABLE=1.99.0               # released 2026-10-01; keep equal to rust-toolchain.toml in bayan-core and bayan-server
RUST_NIGHTLY=nightly-2026-10-02  # only for fuzzing with cargo-fuzz
NODE_VERSION=24.21.0             # Active LTS, released 2026-09-07
NODE_SHA256=fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6
PNPM_VERSION=12.8.2              # released 2026-09-30 (12.9.x was younger than 24 hours); inside a repository, pnpm switches itself to that repository's pinned version
# SHA-512 of pnpm's native Linux binary package, @pnpm/exe.linux-x64 12.8.2 (the npm registry's integrity sha512-2rjP1HbpSMeSyfbP2CcGG0L2+r+9gHKAjYCZZQj/3SdQBywugJ9aa5OWyPp6yz0Z5xd7tKdUtQJh09TnZOUhwA==, in hex)
PNPM_SHA512=dab8cfd476e948c792c9f6cfd827061b42f6fabfbd8072808d80996508ffdd2750072c2e809f5a6b9396c8fa7acb3d19e7177bb4a754b50261d3d4e764e521c0
QT_VERSION=6.12.0                # released 2026-09-30; LGPL modules only (ADR-0013)
QT_ARCHIVES="qtbase qtdeclarative qtsvg qttranslations icu"

# Release binaries: name, version, URL, SHA-256, path of the binary inside the archive, and the source to build from if the download is refused. Dates are publish dates; "published hash" means the hash matches the checksum file of the release.
BINARIES=(
  # 2026-07-09, published hash
  "cargo-deny 0.20.2 https://github.com/EmbarkStudios/cargo-deny/releases/download/0.20.2/cargo-deny-0.20.2-x86_64-unknown-linux-musl.tar.gz 9f12ed4c49936e09b48bf862b595cde2fe64fcbd9d74dfacac6131ca824c8d5f cargo-deny-0.20.2-x86_64-unknown-linux-musl/cargo-deny crate:cargo-deny"
  # 2026-07-06 (the release publishes no checksum file)
  "mdbook 0.5.4 https://github.com/rust-lang/mdBook/releases/download/v0.5.4/mdbook-v0.5.4-x86_64-unknown-linux-musl.tar.gz 5222beabd3e37dc5be0d18ff99b79058469354db5c220153a1b92db5ba12be89 mdbook crate:mdbook"
  # 2026-05-01, published hash
  "lychee 0.24.2 https://github.com/lycheeverse/lychee/releases/download/lychee-v0.24.2/lychee-x86_64-unknown-linux-musl.tar.gz 73657a111819a30c47c08352896796f23d64e4eb2b3ed39b6d32149241566fc5 lychee-x86_64-unknown-linux-musl/lychee crate:lychee"
  # 2026-06-09 (the release publishes no checksum file)
  "cargo-fuzz 0.13.2 https://github.com/rust-fuzz/cargo-fuzz/releases/download/0.13.2/cargo-fuzz-0.13.2-x86_64-unknown-linux-musl.tar.gz b5b704018b63e0f151c17a057ac53b5111e1db545d1b9f72fee79f08a545931c cargo-fuzz crate:cargo-fuzz"
  # 2026-07-30, published hash
  "pinact 4.1.1 https://github.com/suzuki-shunsuke/pinact/releases/download/v4.1.1/pinact_linux_amd64.tar.gz d1cffebe5704b74e2e5f8a864efb9f7e54768972dc686188c008033fb1797841 pinact go:github.com/suzuki-shunsuke/pinact/v4/cmd/pinact"
)

# Python tools, one virtual environment each. Generated with scripts/python-tool-hashes.py (cutoff 2026-10-03T00:00:00Z): only wheels that CPython 3.11-3.14 can install on Ubuntu 24.04 are listed, plus a source archive where no wheel fits.
req_poetry_core() { cat <<'EOF'
poetry-core==2.5.0 \
    --hash=sha256:98ee465b66f7e14bb9fbe68fb5e00d0cff184f036993ec94610ae4b5612f3add
EOF
}
req_reuse() { cat <<'EOF'
attrs==26.1.0 \
    --hash=sha256:c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309
boolean-py==5.0 \
    --hash=sha256:ef28a70bd43115208441b53a045d1549e2f0ec6e3d08a9d142cbc41c1938e8d9
click==8.5.0 \
    --hash=sha256:255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360
jinja2==3.1.6 \
    --hash=sha256:85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67
license-expression==30.4.4 \
    --hash=sha256:421788fdcadb41f049d2dc934ce666626265aeccefddd25e162a26f23bcbf8a4
markupsafe==3.0.4 \
    --hash=sha256:434139499bb20b502ed3baa1f169e618f924a97e7a777fea1a49446d80106cf6 \
    --hash=sha256:6da83a088f8ef93b2d483a8232a4dbf4d69d3d8496b568a03c56becac43e1808 \
    --hash=sha256:8e124f974786f831d6043728e38296969d3579db8896fe004682f5758e613581 \
    --hash=sha256:a8e9f292fcda89b324f2f5c91d13f1424a153e40fc2756f38ee23b15835ff300 \
    --hash=sha256:b4a635a0487774f841cb1fb62e907e7195cc95bc761e053184b8acc3ceb20733
python-debian==1.1.1 \
    --hash=sha256:f98ae013e8e5310e49041cc3860a7105df73af73d4ff1d8afb474770d328a6ad
python-magic==0.4.27 \
    --hash=sha256:c212960ad306f700aa0d01e5d7a325d20548ff97eb9920dcd29513174f0294d3
reuse==6.2.0 \
    --hash=sha256:4feae057a2334c9a513e6933cdb9be819d8b822f3b5b435a36138bd218897d23
tomlkit==0.15.1 \
    --hash=sha256:177a05aece5a8ca5266fd3c448abb47b8d352f09d477d3ca8332db4d89b24304
EOF
}
req_zizmor() { cat <<'EOF'
zizmor==1.30.1 \
    --hash=sha256:eee12266b793cb87ad4a7e3af2e72404f8a63e3de5eb099b80bf7b1cfd232a8e
EOF
}
req_typos() { cat <<'EOF'
typos==1.50.3 \
    --hash=sha256:c26ab14bad1464c9c8931db5e4ca4d1864c00f47362e4ce5ce1f8627074eb524
EOF
}
req_aqtinstall() { cat <<'EOF'
aqtinstall==3.3.0 \
    --hash=sha256:e88dbd87226f276fdd5d05347a44578d390d93a7f176e9476fbda0a7c9635f69
backports-zstd==1.7.0 ; python_full_version < '3.14' \
    --hash=sha256:470895d0bcddc850766e593d1b26764fb138c2feed149f515a2627ef9587d54c \
    --hash=sha256:b2e505d8923e1e9224cf249b99c92cf728e9eb91fbd1e07a9c2816013621fad3 \
    --hash=sha256:f3f4887a8a1fd1290017fe5a1d29a7d1dc5c57f9477fbd64f119316a7e3ae769
beautifulsoup4==4.15.0 \
    --hash=sha256:d6f88de62e1d4e38ecb1077eb9724cd0eff29d2a08ca16a401e9b9e93f117cf9
brotli==1.2.0 ; platform_python_implementation == 'CPython' \
    --hash=sha256:072e7624b1fc4d601036ab3f4f27942ef772887e876beff0301d261210bca97f \
    --hash=sha256:40d918bce2b427a0c4ba189df7a006ac0c7277c180aee4617d99e9ccaaf59e6a \
    --hash=sha256:67a91c5187e1eec76a61625c77a6c8c785650f5b576ca732bd33ef58b0dff49c \
    --hash=sha256:cf9cba6f5b78a2071ec6fb1e7bd39acf35071d90a81231d67e92d637776a6a63
bs4==0.0.2 \
    --hash=sha256:abf8742c0805ef7f662dce4b51cca104cffe52b835238afc169142ab9b3fbccc
certifi==2026.7.22 \
    --hash=sha256:62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775
charset-normalizer==3.5.2 \
    --hash=sha256:1c50fe28bbc2ced33386f298650d91218076c05420e6cbd790b913adc41659e7 \
    --hash=sha256:211d5a3eb6af8f513b8d4ca19a8c1b7accab1b5f0d3175f9826b03c1a920dc1f \
    --hash=sha256:34276fd796040bf0993ab33a369aa572e6979c7aab225a88893667ad8eac8f7a \
    --hash=sha256:3d31298449090ab8d47b7b1b2a555ff73cac7ed438a08b7ac160980c7ebed649 \
    --hash=sha256:6bd128f206a7752ae1f2ab6c61bf8a24ba28913a10df8b14c2637b973ff97a80 \
    --hash=sha256:7218e8f32b0956cfcd048fd42d9d5779809745ca1d86113ca56f66e7ae1549c4 \
    --hash=sha256:b6b751274acb69d77b3323d6b7dbaa3c7fdfc1eb829b7eb61d262f32e1af9685
defusedxml==0.7.1 \
    --hash=sha256:a352e7e428770286cc899e2542b6cdaedb2b4953ff269a210103ec58f6198a61
humanize==4.16.0 \
    --hash=sha256:353eb2f34c09d098b2880eee8bef21832eae6d174f48c5762fff7e5fcb74d01d
idna==3.20 \
    --hash=sha256:ab7ae7122974553370f0bdb919e1a960b2cd1bc1ef0276416d896db81c14582c
inflate64==1.0.4 \
    --hash=sha256:61f51f80fa6f367288343c1a2cd20a42af454883087064e9274fd2a8c3a5a200 \
    --hash=sha256:62d1aac3aba094ae42e27ce7581b414c90f218248be0953b6aeb11a127225e5d \
    --hash=sha256:6f0993214dea0738c557fa56c13cd9083aef0097a201d726c21984ad7f577514 \
    --hash=sha256:ec40c0383cbd84d845dcb785a48ae76eef43246c923f84fda380fdd5ea653d3c \
    --hash=sha256:f62a13d0327631778fa2a47c308ae2b07b2659b7bb8564783259ac65949f8c0c
multivolumefile==0.2.3 \
    --hash=sha256:237f4353b60af1703087cf7725755a1f6fcaeeea48421e1896940cd1c920d678
patch-ng==1.19.1 \
    --hash=sha256:d45fd47b3f74b48c3e336690341876bb26244a077a06f5f7e6e47c19c15c1ca4
psutil==7.2.2 ; sys_platform != 'cygwin' \
    --hash=sha256:076a2d2f923fd4821644f5ba89f059523da90dc9014e85f8e45a5774ca5bc6f9 \
    --hash=sha256:1a571f2330c966c62aeda00dd24620425d4b0cc86881c89861fbc04549e5dc63 \
    --hash=sha256:1fa4ecf83bcdf6e6c8f4449aff98eefb5d0604bf88cb883d7da3d8d2d909546a
py7zr==1.1.3 \
    --hash=sha256:17934a35089e026dec6c72ee275d9b841e646881ef822d618e805c3006661d9a
pybcj==1.0.8 \
    --hash=sha256:0de1f6c90178f5947e4b578821aa2f1f87a78a761ae603aa33a8ad3d8b9b9cac \
    --hash=sha256:3817997e73d60ccbc731a47e007fe02213eee816cfe6070eb8347c6286aa3cc2 \
    --hash=sha256:a50b58f9b9d9978c55e3219b6816a1021a778b028a810b36aa754407591cb5ae \
    --hash=sha256:e5e67ec32176985bbf941185319a3fe385527b6826d457a8ec67dd43b5f0b5fa \
    --hash=sha256:f23a36e978f4620db473b08239ab56dc57a479c83fd5d3808bc95e5bdbc1a703
pycryptodomex==3.23.0 \
    --hash=sha256:a33986a0066860f7fcf7c7bd2bc804fa90e434183645595ae7b33d01f3c91ed8 \
    --hash=sha256:f489c4765093fb60e2edafdf223397bc716491b2b69fe74367b70d6999257a5c
pyppmd==1.3.1 \
    --hash=sha256:1bd6d179ad39b6191ca0cbe62fb9592f33f49277b4384ad7bc5eb0e6ca27ebee \
    --hash=sha256:385e92c97c42e8a6f0bfc0e4acfc6c074cb1ba3a2f650f292696dd9f19e2e603 \
    --hash=sha256:89730cf026416ae2546c92738966ecf117c8176d52c229ad621a61c34643818b \
    --hash=sha256:bd00522ddfcc292304577386b6c217758c0c10e1fb9ce7877ad7d3b7b821a808 \
    --hash=sha256:d1683e6d1ba09e377e0ae02de3a518191a3d63ccdb0b6037c74e6ddf577b5644
requests==2.34.2 \
    --hash=sha256:2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0
semantic-version==2.10.0 \
    --hash=sha256:de78a3b8e0feda74cabc54aab2da702113e33ac9d9eb9d2389bcf1f58b7d9177
soupsieve==2.10 \
    --hash=sha256:8596eb8967d744174820280fa62b4542a2e955bfaccca73ed8a13c6eb8e9b502
texttable==1.7.0 \
    --hash=sha256:72227d592c82b3d7f672731ae73e4d1f88cd8e2ef5b075a7a7f01a23a3743917
typing-extensions==4.16.0 \
    --hash=sha256:481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8
urllib3==2.8.0 \
    --hash=sha256:0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3
EOF
}

# ---------------------------------------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------------------------------------
TOOLS=/opt/bayandocs
LOG_DIR=/var/log/bayandocs-setup
mkdir -p "$TOOLS" "$LOG_DIR"
: >"$LOG_DIR/status.txt"
declare -A JOBS=()

note() { printf '%-7s %-12s %s\n' "$1" "$2" "${3:-}" >>"$LOG_DIR/status.txt"; }

# Run a step in the background with `set -e`, logging to its own file.
start() {
  local name=$1
  shift
  (set -e; "$@") >>"$LOG_DIR/$name.log" 2>&1 &
  JOBS[$name]=$!
}

# Wait for a step; record a failure if it did not succeed.
finish() {
  local name=$1 rc=0
  wait "${JOBS[$name]}" || rc=$?
  unset "JOBS[$name]"
  [ "$rc" -eq 0 ] || note FAILED "$name" "exit code $rc; see $LOG_DIR/$name.log"
  return "$rc"
}

# Download over HTTPS and verify the SHA-256 hash. Returns 2 if the download fails and 3 if the hash does not match.
fetch() {
  local url=$1 sha=$2 out=$3
  curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location --retry 3 --retry-delay 2 \
    --connect-timeout 20 --max-time 300 --output "$out" "$url" || return 2
  echo "$sha  $out" | sha256sum --check --status || { echo "SHA-256 mismatch for $url" >&2; return 3; }
}

# The same, for downloads whose publisher states a SHA-512 hash (npm packages). Returns 2 if the download fails and 3 if the hash does not match.
fetch_sha512() {
  local url=$1 sha=$2 out=$3
  curl --proto '=https' --tlsv1.2 --fail --silent --show-error --location --retry 3 --retry-delay 2 \
    --connect-timeout 20 --max-time 300 --output "$out" "$url" || return 2
  echo "$sha  $out" | sha512sum --check --status || { echo "SHA-512 mismatch for $url" >&2; return 3; }
}

# ---------------------------------------------------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------------------------------------------------
step_apt() {
  # Development headers that Qt 6 needs to build and run headless, plus ShellCheck for scripts.
  local package missing=""
  for package in $APT_PACKAGES; do
    dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed' || missing="$missing $package"
  done
  if [ -n "$missing" ]; then
    timeout 200 apt-get -o DPkg::Lock::Timeout=60 -o Acquire::Retries=3 update --snapshot "$APT_SNAPSHOT"
    # shellcheck disable=SC2086
    timeout 200 apt-get -o DPkg::Lock::Timeout=60 install -y --no-install-recommends --snapshot "$APT_SNAPSHOT" $APT_PACKAGES
    apt-get clean
  fi
  note ok apt "Qt build headers and shellcheck (Ubuntu snapshot $APT_SNAPSHOT)"
}

step_rust() {
  command -v rustup >/dev/null || { echo "rustup is not installed in this image" >&2; return 1; }
  rustup set auto-self-update disable
  timeout 240 rustup toolchain install "$RUST_STABLE" --profile minimal --component clippy,rustfmt \
    --target wasm32-unknown-unknown --no-self-update
  rustup default "$RUST_STABLE"
  note ok rust "$RUST_STABLE (default) with clippy, rustfmt, wasm32-unknown-unknown"
  timeout 240 rustup toolchain install "$RUST_NIGHTLY" --profile minimal --no-self-update
  note ok rust-nightly "$RUST_NIGHTLY (fuzzing only)"
  # Cargo enforces the 24-hour minimum age natively from Rust 1.100 (ADR-0017); older versions only warn about the setting.
  local minor config="${CARGO_HOME:-$HOME/.cargo}/config.toml"
  minor=$(cut -d. -f2 <<<"$RUST_STABLE")
  if [ "$minor" -ge 100 ] && ! grep -qs 'global-min-publish-age' "$config"; then
    printf '\n[registry]\nglobal-min-publish-age = "1 day"\n' >>"$config"
  fi
}

# Install one release binary; if the download is refused, leave a note so that it is built from source later.
install_binary() {
  local name=$1 version=$2 url=$3 sha=$4 member=$5 source=$6 dir="$TOOLS/$1-$2" tmp rc=0
  if [ ! -x "$dir/$name" ]; then
    tmp=$(mktemp -d)
    fetch "$url" "$sha" "$tmp/archive.tar.gz" || rc=$?
    if [ "$rc" -eq 2 ]; then
      echo "$name $version $source" >"$LOG_DIR/pending-$name"
      note later "$name" "download refused; building $version from source"
      rm -rf -- "$tmp"
      return 0
    fi
    [ "$rc" -eq 0 ] || { rm -rf -- "$tmp"; return "$rc"; }
    tar -xzf "$tmp/archive.tar.gz" -C "$tmp" --no-same-owner "$member"
    install -D -m 0755 "$tmp/$member" "$dir/$name"
    rm -rf -- "$tmp"
  fi
  ln -sfn "$dir/$name" "/usr/local/bin/$name"
  note ok "$name" "$version"
}

# Fallback: build a tool from source when its release download was refused. Cargo checks every crate against Cargo.lock (`--locked`), and Go checks every module against the checksum database, so integrity still holds.
build_from_source() {
  local name=$1 version=$2 source=$3 dir="$TOOLS/$1-$2"
  case "$source" in
    crate:*)
      timeout 280 cargo "+$RUST_STABLE" install --locked --quiet --root "$dir.build" --version "$version" "${source#crate:}"
      install -D -m 0755 "$dir.build/bin/$name" "$dir/$name"
      rm -rf -- "$dir.build"
      ;;
    go:*)
      GOBIN="$dir" GOFLAGS=-trimpath timeout 280 go install "${source#go:}@v$version"
      ;;
  esac
  ln -sfn "$dir/$name" "/usr/local/bin/$name"
  rm -f -- "$LOG_DIR/pending-$name"
  note ok "$name" "$version (built from source)"
}

step_node() {
  local dir="/opt/node-v$NODE_VERSION-linux-x64" pnpm_dir="/opt/pnpm-$PNPM_VERSION" tmp
  if [ "$("$dir/bin/node" --version 2>/dev/null)" != "v$NODE_VERSION" ]; then
    tmp=$(mktemp -d)
    fetch "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.xz" "$NODE_SHA256" "$tmp/node.tar.xz"
    tar -xJf "$tmp/node.tar.xz" -C /opt --no-same-owner
    rm -rf -- "$tmp"
  fi
  ln -sfn "$dir" "$TOOLS/node"
  # pnpm's native binary, from its npm package @pnpm/exe.linux-x64, checked against the SHA-512 pinned above. Corepack is not used: Node.js 25 and later no longer ship it, and it checked only pnpm's small JavaScript wrapper, not the native binary that does the work. Inside each repository, this pnpm switches itself to the version pinned in the repository's packageManager field, verified against the repository's lockfile and npm's signature.
  if [ "$(cat "$pnpm_dir/.bayandocs-sha512" 2>/dev/null)" != "$PNPM_SHA512" ] || [ ! -x "$pnpm_dir/pnpm" ]; then
    tmp=$(mktemp -d)
    fetch_sha512 "https://registry.npmjs.org/@pnpm/exe.linux-x64/-/exe.linux-x64-$PNPM_VERSION.tgz" "$PNPM_SHA512" "$tmp/pnpm.tgz"
    tar -xzf "$tmp/pnpm.tgz" -C "$tmp" package/pnpm
    rm -rf -- "$pnpm_dir"
    mkdir -p "$pnpm_dir"
    install -m 0755 "$tmp/package/pnpm" "$pnpm_dir/pnpm"
    echo "$PNPM_SHA512" >"$pnpm_dir/.bayandocs-sha512"
    rm -rf -- "$tmp"
  fi
  ln -sfn "$pnpm_dir" "$TOOLS/pnpm"
  # Passive fence: never run dependency install scripts (pnpm also blocks dependency builds by default).
  grep -qsx 'ignore-scripts=true' "$HOME/.npmrc" || echo 'ignore-scripts=true' >>"$HOME/.npmrc"
  note ok node "$NODE_VERSION (default node); pnpm $PNPM_VERSION native binary, SHA-512 checked (switches to each repository's pinned pnpm)"
}

# Create a virtual environment for one Python tool from hash-pinned requirements and link its commands. The environment's directory name includes a hash of the requirements, so changing a pin always produces a fresh environment.
install_python_tool() {
  local name=$1 commands=$2 requirements=$3 from_source=${4:-} version digest venv command
  version=$("$requirements" | sed -n "s/^$name==\([^ ]*\).*/\1/p")
  digest=$("$requirements" | sha256sum | cut -c1-12)
  venv="$TOOLS/python/$name-$version-$digest"
  if [ ! -x "$venv/bin/${commands%% *}" ]; then
    rm -rf -- "$venv"
    python3 -m venv "$venv"
    local pip=("$venv/bin/pip" install --no-input --no-cache-dir --timeout 60 --retries 3 --require-hashes)
    "$requirements" >"$venv/requirements.txt"
    if [ -n "$from_source" ]; then
      # No wheel fits this platform: build from the hash-pinned source archive with a hash-pinned build backend.
      req_poetry_core >"$venv/build-requirements.txt"
      timeout 200 "${pip[@]}" --only-binary :all: -r "$venv/build-requirements.txt"
      timeout 200 "${pip[@]}" --no-build-isolation --only-binary :all: --no-binary "$from_source" -r "$venv/requirements.txt"
    else
      timeout 200 "${pip[@]}" --only-binary :all: -r "$venv/requirements.txt"
    fi
  fi
  for command in $commands; do ln -sfn "$venv/bin/$command" "/usr/local/bin/$command"; done
  note ok "$name" "$version"
}

step_qt() {
  local prefix="/opt/Qt/$QT_VERSION/gcc_64"
  if [ "$(cat "$prefix/.bayandocs-archives" 2>/dev/null)" != "$QT_ARCHIVES" ]; then
    # Archives come from Qt's own master server; aqtinstall checks each one against its hash on download.qt.io.
    mkdir -p /opt/Qt && cd /opt/Qt # aqtinstall writes aqtinstall.log into the current directory
    # shellcheck disable=SC2086
    timeout 240 /usr/local/bin/aqt install-qt linux desktop "$QT_VERSION" linux_gcc_64 \
      --base https://master.qt.io --outputdir /opt/Qt --archives $QT_ARCHIVES
    echo "$QT_ARCHIVES" >"$prefix/.bayandocs-archives"
  fi
  note ok qt "$QT_VERSION in $prefix ($QT_ARCHIVES)"
}

write_profile() {
  cat >/etc/profile.d/zz-bayandocs.sh <<EOF
# Written by the BayanDocs cloud environment setup script ($SCRIPT_VERSION).
case ":\$PATH:" in *":\$HOME/.cargo/bin:"*) ;; *) export PATH="\$HOME/.cargo/bin:\$PATH" ;; esac
export PATH="$TOOLS/pnpm:$TOOLS/node/bin:\$PATH"
export QT_ROOT_DIR="/opt/Qt/$QT_VERSION/gcc_64"
export CMAKE_PREFIX_PATH="/opt/Qt/$QT_VERSION/gcc_64\${CMAKE_PREFIX_PATH:+:\$CMAKE_PREFIX_PATH}"
export QT_QPA_PLATFORM=offscreen
case "\${LANG:-C}" in C|POSIX) export LANG=C.UTF-8 ;; esac
EOF
  cat >/usr/local/bin/bayandocs-tools <<'EOF'
#!/bin/sh
# Shows what the BayanDocs cloud environment setup script installed (logs: /var/log/bayandocs-setup/).
cat /var/log/bayandocs-setup/summary.txt 2>/dev/null || echo "The BayanDocs setup script has not run in this environment."
EOF
  chmod 0755 /usr/local/bin/bayandocs-tools
}

# ---------------------------------------------------------------------------------------------------------------------
# Main: independent steps run in parallel to stay well inside the five-minute caching limit.
# ---------------------------------------------------------------------------------------------------------------------
started=$(date +%s)
# Whatever happens, never fail the session start.
trap 'rc=$?; [ "$rc" -eq 0 ] || echo "BayanDocs setup stopped early (exit code $rc); see $LOG_DIR" | tee -a "$LOG_DIR/summary.txt"; exit 0' EXIT
echo "BayanDocs setup $SCRIPT_VERSION: installing tools (logs in $LOG_DIR)"
rm -f -- "$LOG_DIR"/pending-*

start apt step_apt
start rust step_rust
start node step_node
for spec in "${BINARIES[@]}"; do
  read -r name _ <<<"$spec"
  # shellcheck disable=SC2086
  start "$name" install_binary $spec
done
start reuse install_python_tool reuse reuse req_reuse reuse
start zizmor install_python_tool zizmor zizmor req_zizmor
start typos install_python_tool typos typos req_typos
start aqtinstall install_python_tool aqtinstall aqt req_aqtinstall

if finish aqtinstall; then start qt step_qt; else note FAILED qt "skipped because aqtinstall failed"; fi
for spec in "${BINARIES[@]}"; do
  read -r name _ <<<"$spec"
  finish "$name" || true
done
rust_ok=true
finish rust || rust_ok=false

# Build from source any release binary whose download was refused (needs the Rust and Go toolchains).
for pending in "$LOG_DIR"/pending-*; do
  [ -e "$pending" ] || continue
  read -r name version source <"$pending"
  if [ "${source%%:*}" = crate ] && ! $rust_ok; then
    note FAILED "$name" "not built: the Rust toolchain step failed"
    continue
  fi
  start "$name-source" build_from_source "$name" "$version" "$source"
done
for name in "${!JOBS[@]}"; do finish "$name" || true; done

# bayan-desktop pins its own CMake, Ninja, clang-format and clang-tidy (with hashes) and installs them with its scripts/dev-setup.sh, which reuses the Qt installed above. Repositories are cloned before this script runs; in sessions without bayan-desktop this does nothing.
# The tools are deliberately not linked into /usr/local/bin: the pinned CMake is version 4, which refuses projects that declare cmake_minimum_required below 3.5 (as some C and C++ code that Rust build scripts compile still does), so it must not become the cmake of every repository. Agents working on bayan-desktop load its environment file first, as that repository's AGENTS.md says.
DESKTOP_TOOLS="$HOME/.local/share/bayandocs/desktop-tools"
if [ -x /home/user/bayan-desktop/scripts/dev-setup.sh ]; then
  if BAYAN_TOOLS_DIR="$DESKTOP_TOOLS" /home/user/bayan-desktop/scripts/dev-setup.sh >"$LOG_DIR/desktop-tools.log" 2>&1; then
    note ok desktop-tools "bayan-desktop's pinned build tools (scripts/dev-setup.sh); to use them: . $DESKTOP_TOOLS/env.sh"
  else
    note FAILED desktop-tools "see $LOG_DIR/desktop-tools.log"
  fi
fi

write_profile
{
  echo "BayanDocs cloud environment, setup script $SCRIPT_VERSION, finished $(date -u +%Y-%m-%dT%H:%MZ) in $(($(date +%s) - started)) s"
  grep -v '^later' "$LOG_DIR/status.txt" | sort -k2,2
} >"$LOG_DIR/summary.txt"
cat "$LOG_DIR/summary.txt"
if [ -x /home/user/bayan-web/scripts/dev-setup.sh ]; then /home/user/bayan-web/scripts/dev-setup.sh >/var/log/bayandocs-setup/bayan-web.log 2>&1 || echo "bayan-web dev-setup failed; see /var/log/bayandocs-setup/bayan-web.log"; fi
# pip-audit, for the supply-chain check of the Python tools' pins (.github/supply-chain/ in every repository, work package X-003): installed by this repository's scripts/dev-setup.sh from the hash-pinned .github/supply-chain/pip-audit-requirements.txt into /root/.local/share/bayandocs, and linked as /root/.local/bin/pip-audit. It does nothing when the docs repository is not attached.
if [ -x /home/user/docs/scripts/dev-setup.sh ]; then /home/user/docs/scripts/dev-setup.sh --pip-audit >/var/log/bayandocs-setup/pip-audit.log 2>&1 || echo "pip-audit setup failed; see /var/log/bayandocs-setup/pip-audit.log"; fi
exit 0
