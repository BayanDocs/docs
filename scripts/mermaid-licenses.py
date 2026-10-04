#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Lists every package whose code is inside a Mermaid release's dist/mermaid.min.js, with its license and copyright notices, and can write site/mermaid/THIRD-PARTY-NOTICES.txt from that list. Run it in the monthly dependency session whenever the vendored Mermaid script is updated (site/mermaid/README.md).
#
# Why a script: mermaid.min.js is one file built from about seventy packages, and several of those ship prebuilt files that already contain other packages (Mermaid's own parser carries langium, chevrotain and the vscode-languageserver libraries, for example). The dependency tree that `pnpm licenses list` shows misses those, and it also lists packages whose code is not in the file. So this script reads the build's own records instead:
#   1. dist/mermaid.js, the unminified build published next to mermaid.min.js, names the source file of every module it contains. Modules whose code the build dropped (left as empty "use strict" wrappers) are not counted.
#   2. When a bundled file was itself prebuilt from other packages, the source map published next to it names those packages. Webpack bundles name their inlined packages in their module paths. For other prebuilt files without a source map, REVIEWED below records what a person found inside them, and the script stops if a bundled package version has not been reviewed yet.
#   3. Every package is downloaded from the npm registry and checked against the registry's integrity hash; its license and copyright lines are read from its own files.
# The script fails if the release is younger than 24 hours, if its bundle contains the ELK layout engine (EPL-2.0), or if any package's license is not on the ADR-0017 allowlist.
#
# Usage: python3 scripts/mermaid-licenses.py VERSION [--write]
#   Without --write it only reports, including whether the vendored files are up to date.
#   With --write it installs that release's mermaid.min.js (the downloaded, integrity-checked bytes) into site/mermaid/, updates SHA256SUMS and the Subresource Integrity hash in mermaid-init.js, and rewrites THIRD-PARTY-NOTICES.txt. It does not edit REUSE.toml or LICENSES/: it reports what they need, so that a person sees every change of license.
# Only Python's standard library is used; downloads come from registry.npmjs.org.

import base64
import datetime
import hashlib
import io
import json
import re
import sys
import tarfile
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOTICES = REPO / "site" / "mermaid" / "THIRD-PARTY-NOTICES.txt"
VENDORED = REPO / "site" / "mermaid" / "mermaid.min.js"
CHECKSUMS = REPO / "site" / "mermaid" / "SHA256SUMS"
LOADER = REPO / "site" / "mermaid" / "mermaid-init.js"
REGISTRY = "https://registry.npmjs.org"
MINIMUM_AGE = datetime.timedelta(hours=24)

# The license allowlist of ADR-0017 (policy 8) for code.
ALLOWLIST = {"MIT", "MIT-0", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Zlib", "0BSD", "BSL-1.0", "CC0-1.0", "Unicode-3.0", "Unicode-DFS-2016", "MPL-2.0"}

# Packages whose package.json has no usable license field; the value was read from the package's LICENSE file by a person.
LICENSE_FIXES = {
    ("khroma", "2.1.0"): "MIT",
}

# Prebuilt files without a source map: what a person found inlined in them, per package version. Each entry is (name, version used to read the license, version shown in the notices). Add an entry, after looking inside the file, whenever the script asks for one; an empty list means "nothing from other packages".
REVIEWED = {
    # bundled/rough.esm.js imports nothing: it contains its four dependencies, at the only versions in range when 4.6.6 was built (2023-11-20).
    ("roughjs", "4.6.6"): [("hachure-fill", "0.5.2", "0.5.2"), ("path-data-parser", "0.1.0", "0.1.0"), ("points-on-curve", "0.2.0", "0.2.0"), ("points-on-path", "0.2.1", "0.2.1")],
    # build/venn.esm.js contains fmin's optimizers (nelderMead, conjugateGradient); package.json pins fmin 0.0.4 (patched) as a development dependency.
    ("@upsetjs/venn.js", "2.0.0"): [("fmin", "0.0.4", "0.0.4")],
    # dist/cytoscape.esm.mjs contains the heap package (CoffeeScript priority queue) and lodash's debounce, memoize and hash helpers. Its build records no exact versions: heap ^0.2.7 has only 0.2.7; lodash ^4.17.21 has the same license and notice in every 4.x release. The legal comments it keeps for smaller embedded snippets stay inside the bundle.
    ("cytoscape", "3.34.0"): [("heap", "0.2.7", "0.2.7"), ("lodash", "4.17.21", "4.x")],
    # Self-contained bundles: no code from other packages.
    ("katex", "0.16.47"): [],
    ("dayjs", "1.11.21"): [],
    # Compiled one output file per source file (no bundler); the bundled files import only the package's own files.
    ("@braintree/sanitize-url", "7.1.2"): [],
    ("@iconify/utils", "3.0.2"): [],
    ("es-toolkit", "1.45.1"): [],
    ("khroma", "2.1.0"): [],
    ("uuid", "14.0.0"): [],
}

# Webpack source paths inside source maps, which name no package version: (prefix, package, version), where None means generated code that belongs to no package. vscode-uri's own build is a webpack bundle whose sources are named webpack://LIB/...: langium requires vscode-uri ~3.1.0, which has only 3.1.0, and vscode-uri 3.1.0 bundles path-browserify ^1.0.1, which has only 1.0.1.
WEBPACK_SOURCES = [
    ("webpack://LIB/src/", "vscode-uri", "3.1.0"),
    ("webpack://LIB/node_modules/path-browserify/", "path-browserify", "1.0.1"),
    ("webpack://LIB/webpack/", None, None),  # webpack's own module loader
]

# Paths of prebuilt files (as opposed to plain source files) that need a source map or a review.
PREBUILT_DIRS = {"dist", "build", "bundled", "lib", "esm", "cjs", "umd"}

# Esbuild's wrapper lines, which contain no code of the module itself.
WRAPPER_LINE = re.compile(r'^(var init_\w+ = __esm\(\{|var require_\w+ = __commonJS\(\{|"[^"]+"\([^)]*\) \{|"use strict";|init_\w+\(\);|\}\);?|\}|\);?|// .*)$')
MODULE_COMMENT = re.compile(r"^\s*// (\S+\.(?:m?js|cjs|ts))$")
STORE_PATH = re.compile(r"node_modules/\.pnpm/([^/]+)/node_modules/((?:@[^/]+/)?[^/]+)/(.*)$")


def fail(message):
    sys.exit(f"error: {message}")


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


_documents = {}
_tarballs = {}


def package_document(name, version):
    key = (name, version)
    if key not in _documents:
        _documents[key] = json.loads(fetch(f"{REGISTRY}/{urllib.parse.quote(name, safe='@')}/{version}"))
    return _documents[key]


def package_tarball(name, version):
    """Downloads a package and checks it against the registry's integrity hash."""
    key = (name, version)
    if key not in _tarballs:
        dist = package_document(name, version)["dist"]
        data = fetch(dist["tarball"])
        algorithm, expected = dist["integrity"].split("-", 1)
        if algorithm != "sha512" or base64.b64encode(hashlib.sha512(data).digest()).decode() != expected:
            fail(f"{name}@{version} does not match the registry's integrity hash")
        # Kept open in memory (no file on disk) because several functions read from the same package.
        _tarballs[key] = tarfile.open(fileobj=io.BytesIO(data))
    return _tarballs[key]


def read(tar, path):
    try:
        return tar.extractfile(tar.getmember(path)).read()
    except KeyError:
        return None


def root_files(tar):
    """Maps file names directly inside the package folder to their tar member names."""
    files = {}
    for member in tar.getmembers():
        parts = member.name.split("/")
        if len(parts) == 2 and member.isfile():
            files[parts[1]] = member.name
    return files


def license_expression(name, version):
    if (name, version) in LICENSE_FIXES:
        return LICENSE_FIXES[(name, version)]
    value = package_document(name, version).get("license")
    if isinstance(value, dict):
        value = value.get("type")
    if not isinstance(value, str) or not value or value.upper().startswith("SEE LICENSE"):
        fail(f"{name}@{version} has no usable license field; read its LICENSE file and add it to LICENSE_FIXES")
    return value


def allowed(expression):
    """Evaluates an SPDX expression of AND, OR and parentheses against the allowlist."""
    tokens = re.findall(r"\(|\)|[^\s()]+", expression)
    position = 0

    def term():
        nonlocal position
        token = tokens[position]
        position += 1
        if token == "(":
            value = either()
            position += 1  # the closing parenthesis
            return value
        return token in ALLOWLIST

    def both():
        nonlocal position
        value = term()
        while position < len(tokens) and tokens[position] == "AND":
            position += 1
            value = term() and value
        return value

    def either():
        nonlocal position
        value = both()
        while position < len(tokens) and tokens[position] == "OR":
            position += 1
            value = both() or value
        return value

    return either()


# A copyright line starts like one of these; BOILERPLATE excludes the sentences of license texts that start the same way (such as Apache-2.0's "(c) You must retain ...").
COPYRIGHT_LINE = re.compile(r"^(copyright\b|\(c\)|©|original .* copyright:|based on underscore)", re.IGNORECASE)
BOILERPLATE = re.compile(r"copyright (notice|holder|owner|license|law|statement|and related)|above copyright|the copyright|copyright,$|you must|patent claims|derivative works|licensor|\[name of", re.IGNORECASE)


def notices(name, version, bundled_paths=()):
    """Returns the copyright lines of a package and the text of its NOTICE file, if any. The lines come from its license files; if those name nobody, from license comments in its bundled files, then from its author, then from its repository."""
    tar = package_tarball(name, version)
    lines, notice_text = [], None
    for file_name, member in sorted(root_files(tar).items()):
        if not re.match(r"(?i)(licen[cs]e|copying|notice)", file_name) or file_name.endswith((".js", ".mjs", ".cjs", ".ts")):
            continue
        text = read(tar, member).decode("utf-8", "replace")
        if file_name.upper().startswith("NOTICE"):
            notice_text = text.strip()
        text_lines = [line.strip() for line in text.splitlines()]
        for index, line in enumerate(text_lines):
            if not COPYRIGHT_LINE.match(line) or BOILERPLATE.search(line):
                continue
            # A notice that continues on the next line ends with a comma (Lodash: "... copyright Jeremy Ashkenas,").
            if line.endswith(",") and index + 1 < len(text_lines) and text_lines[index + 1]:
                line = f"{line} {text_lines[index + 1]}"
            if line not in lines:
                lines.append(line)
    if not lines:
        for path in sorted(bundled_paths):
            content = read(tar, f"package/{path}") or b""
            for comment in re.findall(r"/\*[!*]?\s*@license(.*?)\*/", content.decode("utf-8", "replace"), re.DOTALL):
                for part in re.split(r"\s*\|\s*|\n", comment):
                    part = part.strip(" *")
                    if re.match(r"(?i)(\(c\)|©|copyright\b)", part) and part not in lines:
                        lines.append(f"{part} (from the license comment in {path})")
    if not lines:
        document = package_document(name, version)
        author = document.get("author")
        author = author.get("name") if isinstance(author, dict) else author
        repository = document.get("repository")
        repository = repository.get("url") if isinstance(repository, dict) else repository
        if author:
            lines.append(f"{author} (author; the package has no copyright line)")
        elif repository:
            repository = re.sub(r"^(git\+)?(git|ssh|https?)://(git@)?", "https://", repository).removesuffix(".git")
            lines.append(f"(the package names no copyright holder; it comes from {repository})")
        else:
            lines.append("(the package names no copyright holder)")
    return lines, notice_text


def bundled_modules(mermaid_js, mermaid_version, parser_version):
    """Reads esbuild's module comments in dist/mermaid.js: {(package, version): set of file paths inside the package that contain code}."""
    modules, current, code = {}, None, {}
    for line in mermaid_js.splitlines():
        match = MODULE_COMMENT.match(line)
        if match:
            path = match.group(1)
            store = STORE_PATH.search(path)
            if store:
                version = store.group(1).split("_")[0].rsplit("@", 1)[1]
                current = (store.group(2), version, store.group(3))
            elif path.startswith("../parser/"):
                current = ("@mermaid-js/parser", parser_version, path[len("../parser/"):])
            elif not path.startswith("../"):
                current = ("mermaid", mermaid_version, path)
            else:
                fail(f"unexpected module path in dist/mermaid.js: {path}")
            modules.setdefault(current, False)
            continue
        if current and line.strip() and not WRAPPER_LINE.match(line.strip()):
            modules[current] = True
    if not modules:
        fail("dist/mermaid.js has no esbuild module comments; Mermaid's build has changed and this script needs updating")
    for (name, version, path), has_code in modules.items():
        code.setdefault((name, version), {"with_code": set(), "empty": set()})["with_code" if has_code else "empty"].add(path)
    return code


def packages_in_source_map(name, version, path, source_map):
    """Reads the packages named by a source map's "sources" list: {(package, version)}."""
    found = set()
    for source in source_map.get("sources", []):
        store = STORE_PATH.search(source)
        if store:
            found.add((store.group(2), store.group(1).split("_")[0].rsplit("@", 1)[1]))
        elif source.startswith("webpack://"):
            match = next((entry for entry in WEBPACK_SOURCES if source.startswith(entry[0])), None)
            if match is None:
                fail(f"{name}@{version}: unknown webpack source {source} in {path}.map; identify it and add it to WEBPACK_SOURCES")
            if match[1]:
                found.add((match[1], match[2]))
        elif "node_modules/" in source:
            fail(f"{name}@{version}: {path}.map names {source} without a version; identify it and add it to REVIEWED")
    return found


def inlined_packages(name, version, paths):
    """Finds the packages inlined into a package's bundled files. Returns ([(package, version for the license, version shown)], files that need a person to look inside)."""
    tar = package_tarball(name, version)
    found, unexplained = set(), []
    for path in sorted(paths):
        member = f"package/{path}"
        source_map = read(tar, member + ".map")
        if source_map is not None:
            found |= packages_in_source_map(name, version, path, json.loads(source_map))
            continue
        content = read(tar, member)
        if content is None:
            fail(f"{name}@{version} has no file {path}; the version named in dist/mermaid.js is not the published one")
        text = content.decode("utf-8", "replace")
        if "__webpack_require__" in text or "webpackUniversalModuleDefinition" in text:
            # Webpack names every file it bundles; a bundle of the package's own sources names no node_modules folder.
            if "./node_modules/" in text:
                unexplained.append(path)
        elif set(path.split("/")[:-1]) & PREBUILT_DIRS or path.endswith(".min.js"):
            unexplained.append(path)
    inlined = sorted((n, v, v) for n, v in found)
    if unexplained:
        if (name, version) not in REVIEWED:
            return None, unexplained
        inlined = sorted(REVIEWED[(name, version)]) + inlined
    return inlined, []


def main():
    arguments = sys.argv[1:]
    write = "--write" in arguments
    arguments = [a for a in arguments if a != "--write"]
    if len(arguments) != 1:
        sys.exit("usage: python3 scripts/mermaid-licenses.py VERSION [--write]")
    version = arguments[0]

    published = json.loads(fetch(f"{REGISTRY}/mermaid"))["time"][version]
    age = datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
    if age < MINIMUM_AGE:
        fail(f"mermaid {version} was published {published}, less than 24 hours ago (ADR-0017)")
    tar = package_tarball("mermaid", version)
    minified = read(tar, "package/dist/mermaid.min.js")
    mermaid_js = read(tar, "package/dist/mermaid.js")
    if minified is None or mermaid_js is None:
        fail("the package has no dist/mermaid.min.js or dist/mermaid.js")
    if b"org.eclipse.elk" in minified:
        fail("this release bundles the ELK layout engine (elkjs, EPL-2.0), which is not on the ADR-0017 allowlist")
    parser_range = package_document("mermaid", version).get("dependencies", {}).get("@mermaid-js/parser", "")
    parser_version = parser_range.lstrip("^~")

    code = bundled_modules(mermaid_js.decode("utf-8"), version, parser_version)
    entries, dropped, review, bundled = {}, [], [], {}
    for (name, package_version), files in sorted(code.items()):
        if not files["with_code"]:
            dropped.append(f"{name} {package_version}")
            continue
        entries[(name, package_version, package_version)] = None
        bundled[(name, package_version)] = files["with_code"]
        inlined, unexplained = ([], []) if name == "mermaid" else inlined_packages(name, package_version, files["with_code"])
        if unexplained:
            review.append(f"{name} {package_version}: " + ", ".join(unexplained))
            continue
        for inner_name, inner_version, shown in inlined:
            entries.setdefault((inner_name, inner_version, shown), f"{name} {package_version}")
    if review:
        fail("these prebuilt files have no source map; look inside them for code from other packages and record what you find in REVIEWED:\n  " + "\n  ".join(review))

    blocks, licenses, refused = [], set(), []
    for (name, package_version, shown), inside in sorted(entries.items(), key=lambda e: (e[0][0] != "mermaid", e[0][0].lower(), e[0][1])):
        expression = license_expression(name, package_version)
        if not allowed(expression):
            refused.append(f"{name} {package_version}: {expression}")
        licenses.add(expression if " " not in expression else f"({expression.strip('()')})")
        lines, notice_text = notices(name, package_version, bundled.get((name, package_version), ()))
        heading = f"{name} {shown} ({expression.strip('()') if expression.count('(') == 1 and expression.startswith('(') else expression})"
        if inside:
            heading += f", inside {inside}"
        block = [heading] + [f"    {line}" for line in lines]
        if notice_text and expression != "MIT":
            block += ["    NOTICE file:"] + [f"        {line}".rstrip() for line in notice_text.splitlines()]
        blocks.append("\n".join(block))
    if refused:
        fail("licenses not on the ADR-0017 allowlist:\n  " + "\n  ".join(refused))

    order = ["MIT", "ISC", "BSD-3-Clause", "Apache-2.0"]
    spdx = " AND ".join(sorted(licenses, key=lambda expression: (order.index(expression) if expression in order else len(order), expression)))
    sha256 = hashlib.sha256(minified).hexdigest()
    sri = "sha384-" + base64.b64encode(hashlib.sha384(minified).digest()).decode()
    text = f"""Third-party notices for site/mermaid/mermaid.min.js

mermaid.min.js is the unmodified dist/mermaid.min.js file from the npm package mermaid {version} (https://mermaid.js.org, https://www.npmjs.com/package/mermaid). Mermaid's build combines code from the packages below into that one file; some of them were themselves prebuilt with code from other packages, shown as "inside". The full license texts are in the LICENSES folder at the root of this repository. The license comments that the build keeps at the end of mermaid.min.js (DOMPurify, Lodash and code embedded in Cytoscape) are left in place.

This list was generated by scripts/mermaid-licenses.py from the build's own records (see site/mermaid/README.md). It lists only packages whose code is in the file; packages that appear in Mermaid's dependency tree but not in the file are left out.

""" + "\n".join(blocks) + "\n"
    checksums = f"{sha256}  mermaid.min.js\n"
    loader = LOADER.read_text(encoding="utf-8")
    integrity_line = re.compile(r'const MERMAID_INTEGRITY = "sha384-[A-Za-z0-9+/=]+";')
    if not integrity_line.search(loader):
        fail(f"{LOADER.relative_to(REPO)} has no MERMAID_INTEGRITY line to update")
    new_loader = integrity_line.sub(f'const MERMAID_INTEGRITY = "{sri}";', loader)
    if write:
        VENDORED.write_bytes(minified)
        CHECKSUMS.write_text(checksums, encoding="utf-8")
        LOADER.write_text(new_loader, encoding="utf-8")
        NOTICES.write_text(text, encoding="utf-8")
    vendored_files = {
        VENDORED: VENDORED.exists() and VENDORED.read_bytes() == minified,
        CHECKSUMS: CHECKSUMS.exists() and CHECKSUMS.read_text(encoding="utf-8") == checksums,
        LOADER: loader == new_loader or write,
        NOTICES: NOTICES.exists() and NOTICES.read_text(encoding="utf-8") == text,
    }

    # REUSE.toml and LICENSES/ are left to a person; check whether they already match.
    reuse = tomllib.loads((REPO / "REUSE.toml").read_text(encoding="utf-8"))
    recorded = next((a.get("SPDX-License-Identifier") for a in reuse.get("annotations", []) if a.get("path") == "site/mermaid/mermaid.min.js"), None)
    missing_texts = sorted(i for i in set(re.findall(r"[A-Za-z0-9.+-]+", spdx)) - {"AND", "OR"} if not (REPO / "LICENSES" / f"{i}.txt").exists())

    print(f"mermaid {version}, published {published}; tarball integrity checked")
    print(f"dist/mermaid.min.js: SHA-256 {sha256}, Subresource Integrity {sri}")
    print(f"packages with code in the file: {len(entries)}")
    print(f"listed by the build but with no code left in the file (not listed in the notices): {', '.join(dropped) or 'none'}")
    print(f"license expression of the file: {spdx}")
    for path, up_to_date in vendored_files.items():
        print(f"  {path.relative_to(REPO)}: {'written' if write else 'up to date' if up_to_date else 'OUT OF DATE (run with --write)'}")
    problems = []
    if recorded != spdx:
        problems.append(f'REUSE.toml: set SPDX-License-Identifier for site/mermaid/mermaid.min.js to "{spdx}" (it is "{recorded}")')
    if missing_texts:
        problems.append("LICENSES/: add " + ", ".join(missing_texts) + " with `reuse download`")
    for problem in problems:
        print(f"  TO DO: {problem}")
    if problems or (not write and not all(vendored_files.values())):
        sys.exit(1)

if __name__ == "__main__":
    main()
