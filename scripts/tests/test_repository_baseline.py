#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Keeps the repository baseline of work packages X-001 and X-002 in step with the documents it copies:
#   - .github/pull_request_template.md is the hand-off template of plan/06-agent-workflow.md, word for word;
#   - .github/reuse/ pins the same REUSE as the cloud environment (scripts/cloud-environment-setup.sh), so that CI checks with the tool that agent sessions use;
#   - the workflow-lint workflow pins the same zizmor (.github/workflow-lint/requirements.txt) and pinact (.github/workflows/workflow-lint.yml) as the cloud environment, for the same reason.
# The other four repositories carry copies of the same files; the monthly dependency session updates them together.
#
# scripts/verify.sh runs these tests; to run them alone: python3 -m unittest discover -s scripts/tests -v

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def setup_script_requirements(function: str) -> str:
    """The hash-pinned requirements that a req_* function of the cloud environment setup script prints."""
    text = (ROOT / "scripts" / "cloud-environment-setup.sh").read_text(encoding="utf-8")
    match = re.search(rf"^{function}\(\) {{ cat <<'EOF'\n(.*?)\nEOF\n}}", text, re.DOTALL | re.MULTILINE)
    if match is None:
        raise AssertionError(f"{function} is not in scripts/cloud-environment-setup.sh")
    return match.group(1).strip()


def requirements_file(name: str, folder: str = "reuse") -> str:
    """A requirements file of .github/<folder>/ without its comment lines."""
    lines = (ROOT / ".github" / folder / name).read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if not line.startswith("#")).strip()


def setup_script_binary(name: str) -> list[str]:
    """The fields of a BINARIES line of the cloud environment setup script: name, version, URL, SHA-256, path in the archive, fallback source."""
    text = (ROOT / "scripts" / "cloud-environment-setup.sh").read_text(encoding="utf-8")
    lines = re.findall(rf'^  "({re.escape(name)} [^"]*)"$', text, re.MULTILINE)
    if len(lines) != 1:
        raise AssertionError(f"expected one {name} line in BINARIES of scripts/cloud-environment-setup.sh, found {len(lines)}")
    return lines[0].split()


def workflow_env(workflow: str, variable: str) -> str:
    """The value of a variable that a workflow sets in an env: block, which must be set exactly once."""
    text = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    values = re.findall(rf"^\s+{re.escape(variable)}: (\S+)$", text, re.MULTILINE)
    if len(values) != 1:
        raise AssertionError(f"expected {variable} to be set once in .github/workflows/{workflow}, found {len(values)}")
    return values[0]


class PullRequestTemplateTests(unittest.TestCase):
    def test_the_template_is_the_hand_off_template(self) -> None:
        plan = (ROOT / "plan" / "06-agent-workflow.md").read_text(encoding="utf-8")
        section = plan.split("\n## Hand-off template\n", 1)[1]
        match = re.search(r"```markdown\n(.*?)\n```", section, re.DOTALL)
        self.assertIsNotNone(match, "plan/06-agent-workflow.md has no hand-off template in a ```markdown block")
        assert match is not None
        template = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
        self.assertEqual(template, match.group(1) + "\n", "update .github/pull_request_template.md in all five repositories to match plan/06-agent-workflow.md")


class ReusePinTests(unittest.TestCase):
    def test_reuse_is_pinned_like_the_cloud_environment(self) -> None:
        self.assertEqual(requirements_file("requirements.txt"), setup_script_requirements("req_reuse"))

    def test_its_build_backend_is_pinned_like_the_cloud_environment(self) -> None:
        self.assertEqual(requirements_file("build-requirements.txt"), setup_script_requirements("req_poetry_core"))


class WorkflowLintPinTests(unittest.TestCase):
    def test_zizmor_is_pinned_like_the_cloud_environment(self) -> None:
        self.assertEqual(requirements_file("requirements.txt", folder="workflow-lint"), setup_script_requirements("req_zizmor"))

    def test_pinact_is_pinned_like_the_cloud_environment(self) -> None:
        _, version, url, sha256, *_ = setup_script_binary("pinact")
        self.assertEqual(workflow_env("workflow-lint.yml", "PINACT_VERSION"), version)
        self.assertEqual(workflow_env("workflow-lint.yml", "PINACT_SHA256"), sha256)
        # The workflow downloads the same archive as the setup script.
        self.assertEqual(url, f"https://github.com/suzuki-shunsuke/pinact/releases/download/v{version}/pinact_linux_amd64.tar.gz")
        workflow = (ROOT / ".github" / "workflows" / "workflow-lint.yml").read_text(encoding="utf-8")
        self.assertIn('"https://github.com/suzuki-shunsuke/pinact/releases/download/v$PINACT_VERSION/pinact_linux_amd64.tar.gz"', workflow)


if __name__ == "__main__":
    unittest.main()
