#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Tests for the ID check of scripts/verify.sh, the function check_ids: every work package ID that the Markdown mentions must be defined by a brief (workpackages/phase-N/<ID>-<title>.md) or by a draft heading in workpackages/.
# Each test runs the function itself, cut word for word from scripts/verify.sh together with the script's settings line (set -euo pipefail) and its WP_ID pattern, in a made-up repository in a temporary folder.
#
# scripts/verify.sh runs them; to run them alone: python3 -m unittest discover -s scripts/tests -v

from __future__ import annotations

import fcntl
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parents[2]


def verify_sh_part(pattern: str, what: str) -> str:
    """The one part of scripts/verify.sh that the regular expression matches."""
    found = re.findall(pattern, (ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8"), re.MULTILINE | re.DOTALL)
    if len(found) != 1:
        raise AssertionError(f"expected one {what} in scripts/verify.sh, found {len(found)}")
    return found[0]


def check_ids_script() -> str:
    """A bash script that runs check_ids of scripts/verify.sh on the Markdown files given as its arguments, the way scripts/verify.sh runs it (inside an if, with the script's settings), and exits with its result."""
    return "\n".join(
        [
            verify_sh_part(r"^set -[a-z]+ pipefail$", "settings line with pipefail"),
            verify_sh_part(r"^WP_ID='[^'\n]*'$", "WP_ID line"),
            'markdown_files=("$@")',
            verify_sh_part(r"^check_ids\(\) \{\n.*?\n\}$", "check_ids function"),
            "if check_ids; then exit 0; else exit 1; fi",
        ]
    )


def pipe_capacity() -> int:
    """How many bytes a new pipe holds before its writer has to wait for the reader (64 KiB on Linux x86-64)."""
    read_end, write_end = os.pipe()
    try:
        return fcntl.fcntl(write_end, fcntl.F_GETPIPE_SZ)
    finally:
        os.close(read_end)
        os.close(write_end)


class IdCheckTests(unittest.TestCase):
    def check(self, files: Dict[str, str]) -> Tuple[int, str]:
        """Runs check_ids in a new folder that holds these files (path: content). Returns its exit status and everything it printed."""
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for name, content in files.items():
                path = folder / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            markdown_files = sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*.md"))
            result = subprocess.run(["bash", "-c", check_ids_script(), "check_ids", *markdown_files], cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120, check=False)
            return result.returncode, result.stdout

    def test_a_defined_id_is_found_however_long_the_list_of_defined_ids(self) -> None:
        # The regression test for the check's random failures (docs#61, follow-up 9). The check used to look each mentioned ID up with the pipeline  printf '%s\n' "${defined[@]}" | grep -qxF "$id"  under pipefail. bash's printf writes each line with a write() of its own, and grep -q stops reading at its first match; when printf still had lines to write, it died of SIGPIPE, the pipeline failed, and a defined ID was reported as missing.
        # Here the mentioned ID comes first in a list of defined IDs eight times as large as what a pipe holds. When grep -q has found it and stopped, printf can have written at most what grep read plus what the pipe holds, a quarter of the list, so such a pipeline fails here every time, whatever the timing.
        padding = "## X-002 — the same draft again\n" * (8 * pipe_capacity() // len("X-002\n"))
        status, output = self.check({"workpackages/drafts.md": "## X-001 — a draft\n" + padding, "page.md": "X-001 and X-002 are drafts.\n"})
        self.assertEqual((status, output), (0, ""))

    def test_an_id_that_nothing_defines_is_still_reported(self) -> None:
        # The check stays as strict as before: a brief's file name and a draft heading in workpackages/ define an ID; a heading outside workpackages/ does not, and neither does a mention.
        status, output = self.check(
            {
                "workpackages/phase-0/X-001-a-brief.md": "# X-001: a brief\n",
                "workpackages/drafts.md": "### X-002 — a draft\n",
                "notes.md": "## X-003 — a heading outside workpackages/\n\nX-001, X-002 and X-004.\n",
            }
        )
        self.assertEqual(status, 1)
        self.assertEqual(
            output.splitlines(),
            [
                "    X-003 is mentioned, but no work package brief or draft defines it",
                "    X-004 is mentioned, but no work package brief or draft defines it",
            ],
        )


if __name__ == "__main__":
    unittest.main()
