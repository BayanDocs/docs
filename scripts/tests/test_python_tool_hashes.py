#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Tests for scripts/python-tool-hashes.py. They replace uv and PyPI with small stand-ins, so they need no network and no uv: the stand-in for `uv pip compile --universal` behaves like uv in the one way that matters here, by leaving out the dependencies that only Python versions below the lowest supported one need.
#
# scripts/verify.sh runs them; to run them alone: python3 -m unittest discover -s scripts/tests -v

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "python-tool-hashes.py"
_spec = importlib.util.spec_from_file_location("python_tool_hashes", SCRIPT)
assert _spec is not None and _spec.loader is not None
pth = importlib.util.module_from_spec(_spec)
sys.modules["python_tool_hashes"] = pth
_spec.loader.exec_module(pth)

CUTOFF = "2026-10-03T00:00:00Z"
RUNNING_PYTHON = "3.13"  # the Python that this stand-in for uv pretends to run with


def fake_uv(command: List[str], **_kwargs: Any) -> subprocess.CompletedProcess:
    """Answer like `uv pip compile --universal`, whose lowest Python is --python-version or the running Python."""
    lowest = command[command.index("--python-version") + 1] if "--python-version" in command else RUNNING_PYTHON
    lines = ["example-tool==1.0"]
    if tuple(map(int, lowest.split("."))) < (3, 13):
        lines.append("typing-extensions==4.15.0 ; python_full_version < '3.13'")
    lines.append("colorama==0.4.6 ; sys_platform == 'win32'")
    return subprocess.CompletedProcess(command, 0, stdout="\n".join(lines) + "\n", stderr="")


def wheel(filename: str, digest: str) -> Dict[str, Any]:
    return {"packagetype": "bdist_wheel", "filename": filename, "digests": {"sha256": digest}, "upload_time_iso_8601": "2026-09-01T00:00:00.000000Z"}


PYPI = {
    "example-tool/1.0": [wheel("example_tool-1.0-py3-none-any.whl", "a" * 64)],
    "typing-extensions/4.15.0": [wheel("typing_extensions-4.15.0-py3-none-any.whl", "b" * 64)],
}


def fake_urlopen(url: str) -> io.BytesIO:
    name_and_version = url.removeprefix("https://pypi.org/pypi/").removesuffix("/json")
    return io.BytesIO(json.dumps({"urls": PYPI[name_and_version]}).encode())


class ResolutionTests(unittest.TestCase):
    def run_script(self) -> tuple[str, List[List[str]]]:
        commands: List[List[str]] = []

        def recording_uv(command: List[str], **kwargs: Any) -> subprocess.CompletedProcess:
            commands.append(command)
            return fake_uv(command, **kwargs)

        output = io.StringIO()
        with mock.patch.object(pth.subprocess, "run", recording_uv), mock.patch.object(pth.urllib.request, "urlopen", fake_urlopen), mock.patch.object(sys, "argv", ["python-tool-hashes.py", "example-tool==1.0", CUTOFF]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            status = pth.main()
        self.assertEqual(status, 0)
        return output.getvalue(), commands

    def test_resolves_for_the_oldest_supported_python_not_the_running_one(self) -> None:
        # Regression test: without --python-version, uv resolved for the Python it ran with
        # (3.13), so typing-extensions, which cyclonedx-python-lib needs on Python 3.12 and
        # older, was missing and `pip install --require-hashes` failed on Python 3.12.
        output, commands = self.run_script()
        self.assertEqual(len(commands), 1)
        self.assertIn("--universal", commands[0])
        self.assertEqual(commands[0][commands[0].index("--python-version") + 1], f"3.{min(pth.PYTHON_MINORS)}")
        self.assertIn("typing-extensions==4.15.0 ; python_full_version < '3.13' \\\n    --hash=sha256:" + "b" * 64, output)

    def test_keeps_the_hashes_and_drops_requirements_for_other_platforms(self) -> None:
        output, _commands = self.run_script()
        self.assertIn("example-tool==1.0 \\\n    --hash=sha256:" + "a" * 64, output)
        self.assertNotIn("colorama", output)


if __name__ == "__main__":
    unittest.main()
