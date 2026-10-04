#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
"""Print hash-pinned requirements for a Python command-line tool.

Used in the monthly dependency session to refresh the requirement blocks in
scripts/cloud-environment-setup.sh. It resolves the tool and its dependencies
with uv as they were at the cutoff time (which must be at least 24 hours ago,
ADR-0017), then keeps only the SHA-256 hashes of wheels that CPython 3.11-3.14
can install on x86-64 Ubuntu 24.04 (glibc 2.39), so the setup script stays
short. When wheels do not cover all of those Python versions, the hash of the
source archive is added and the package must be built from source.

Usage: python3 scripts/python-tool-hashes.py 'reuse==6.2.0' 2026-10-03T00:00:00Z
Needs: uv on PATH and network access to pypi.org. Standard library only.
"""

import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PYTHON_MINORS = range(11, 15)
GLIBC_MINOR = 39  # Ubuntu 24.04
MANYLINUX = re.compile(r"^manylinux(1|2010|2014|_2_(\d+))_x86_64$")
SKIP_MARKER = re.compile(r"platform_python_implementation == 'PyPy'|sys_platform == '(win32|darwin|cygwin)'")


def platform_ok(tag: str) -> bool:
    if tag == "any":
        return True
    match = MANYLINUX.match(tag)
    return bool(match) and (match.group(2) is None or int(match.group(2)) <= GLIBC_MINOR)


def wheel_minors(filename: str) -> set[int]:
    """Return the CPython 3.x minor versions that can install this wheel."""
    # name-version(-build)?-python-abi-platform.whl; tags may be compressed with "."
    python_tags, abi_tags, platform_tags = filename[: -len(".whl")].split("-")[-3:]
    if not any(platform_ok(tag) for tag in platform_tags.split(".")):
        return set()
    minors: set[int] = set()
    for python_tag in python_tags.split("."):
        if python_tag in ("py3", "py2.py3"):
            minors.update(PYTHON_MINORS)
        elif re.fullmatch(r"cp3\d+", python_tag):
            built_for = int(python_tag[3:])
            if "abi3" in abi_tags.split("."):
                # abi3 wheels built for an older CPython also work on newer ones
                minors.update(m for m in PYTHON_MINORS if m >= built_for)
            elif built_for in PYTHON_MINORS:
                minors.add(built_for)
    return minors


def target_minors(marker: str) -> set[int]:
    """Apply simple Python version bounds from a marker, such as python_full_version < '3.14'."""
    minors = set(PYTHON_MINORS)
    for op, minor in re.findall(r"python(?:_full)?_version\s*(<=|>=|<|>)\s*'3\.(\d+)", marker):
        bound = int(minor)
        keep = {"<": bound.__gt__, "<=": bound.__ge__, ">": bound.__lt__, ">=": bound.__le__}[op]
        minors = {m for m in minors if keep(m)}
    return minors


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    requirement, cutoff = sys.argv[1], sys.argv[2]
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp, "in.txt")
        source.write_text(requirement + "\n")
        resolved = subprocess.run(
            ["uv", "pip", "compile", "-q", "--universal", "--exclude-newer", cutoff,
             "--no-header", "--no-annotate", str(source)],
            check=True, capture_output=True, text=True,
        ).stdout
    for line in resolved.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        spec, _, marker = line.partition(";")
        marker = marker.strip()
        # Drop requirements that only apply to PyPy, Windows, macOS or Cygwin.
        if marker and " or " not in marker and SKIP_MARKER.search(marker):
            continue
        name, version = spec.strip().split("==")
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json") as response:
            files = json.load(response)["urls"]
        files = [f for f in files if f["upload_time_iso_8601"] <= cutoff]
        covered: set[int] = set()
        hashes = []
        for f in files:
            if f["packagetype"] == "bdist_wheel" and (minors := wheel_minors(f["filename"])):
                covered |= minors
                hashes.append(f["digests"]["sha256"])
        if not target_minors(marker) <= covered:
            # Wheels do not cover every target Python (reuse, for example, publishes only a
            # CPython 3.10 wheel): add the source archive; the setup script builds it with
            # --no-binary and a hash-pinned build backend.
            sdists = [f["digests"]["sha256"] for f in files if f["packagetype"] == "sdist"]
            if not sdists:
                print(f"error: no usable file for {name}=={version}", file=sys.stderr)
                return 1
            hashes += sdists
            print(f"note: {name}=={version} must be built from source", file=sys.stderr)
        hashes.sort()
        print(f"{name}=={version}" + (f" ; {marker}" if marker else "") + " \\")
        print(" \\\n".join(f"    --hash=sha256:{digest}" for digest in hashes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
