#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Tests for the external-link check of scripts/verify.sh:
#   - the rules in lychee.toml, run with the pinned lychee and the command line of check_external_links in scripts/verify.sh against a small web server on this machine that answers each link with the status code in its path, so no other site is contacted: rate limits and temporary server errors (429, 503, 504) pass and are not cached, while other error statuses, a missing page, a name that does not resolve and a refused connection fail the check;
#   - scripts/link-report.py, which prints lychee's report, including the answers that lychee accepts although they are not a success.
# The lychee tests are skipped when the pinned lychee is not installed (scripts/dev-setup.sh installs it; scripts/verify.sh checks that it is there before it runs these tests).
#
# scripts/verify.sh runs them; to run them alone: python3 -m unittest discover -s scripts/tests -v

from __future__ import annotations

import contextlib
import http.server
import importlib.util
import io
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location("link_report", ROOT / "scripts" / "link-report.py")
assert _spec is not None and _spec.loader is not None
link_report = importlib.util.module_from_spec(_spec)
sys.modules["link_report"] = link_report
_spec.loader.exec_module(link_report)

# The lychee command line of check_external_links in scripts/verify.sh, word for word (a test below keeps the two equal).
VERIFY_COMMAND = 'lychee --config lychee.toml --cache --scheme https --scheme http --no-progress --verbose --format json --output "$report" --files-from -'

# A name that no DNS server resolves: .internal is reserved for private networks and never delegated (lychee skips .invalid, .test and .example links without checking them, so those cannot be used).
UNRESOLVABLE = "http://bayandocs-link-check.internal/page"


def pinned_lychee_version() -> str:
    """The lychee version in the BINARIES list of scripts/cloud-environment-setup.sh, which scripts/dev-setup.sh installs."""
    text = (ROOT / "scripts" / "cloud-environment-setup.sh").read_text(encoding="utf-8")
    versions = re.findall(r'^  "lychee (\S+) ', text, re.MULTILINE)
    if len(versions) != 1:
        raise AssertionError(f"expected one lychee line in BINARIES of scripts/cloud-environment-setup.sh, found {len(versions)}")
    return versions[0]


def find_lychee() -> Optional[str]:
    """The lychee that scripts/verify.sh would run: the one scripts/dev-setup.sh installed in .tools/bin, else the one on PATH."""
    return shutil.which("lychee", path=os.pathsep.join([str(ROOT / ".tools" / "bin"), os.environ.get("PATH", "")]))


def resolves(url: str) -> bool:
    """True if the host name of the link resolves on this machine."""
    host = url.split("/")[2]
    try:
        socket.getaddrinfo(host, 80)
    except socket.gaierror:
        return False
    return True


def unused_port() -> int:
    """A port on 127.0.0.1 that nothing listens on, so a connection to it is refused."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class StatusServer:
    """A web server on 127.0.0.1 that answers /<status code>/<anything> with that status code."""

    def __init__(self) -> None:
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 (the name http.server requires)
                body = b"<!doctype html><title>test page</title>"
                self.send_response(int(self.path.split("/")[1]))
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_HEAD = do_GET

            def log_message(self, *args: Any) -> None:
                pass

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def url(self, status: int) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/{status}/page"

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


class VerifyCommandTests(unittest.TestCase):
    def test_the_tests_run_lychee_like_verify_sh(self) -> None:
        verify = (ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
        self.assertEqual(verify.count(VERIFY_COMMAND), 1, "VERIFY_COMMAND in scripts/tests/test_link_check.py must be the lychee command line of check_external_links in scripts/verify.sh")


class LycheeConfigurationTests(unittest.TestCase):
    """lychee.toml, as lychee applies it."""

    lychee: str
    server: StatusServer

    @classmethod
    def setUpClass(cls) -> None:
        found = find_lychee()
        if found is None:
            raise unittest.SkipTest("lychee is not installed (scripts/dev-setup.sh installs it)")
        version = subprocess.run([found, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False).stdout.split()
        if version[-1:] != [pinned_lychee_version()]:
            raise unittest.SkipTest(f"{found} is {' '.join(version)}, not the pinned lychee {pinned_lychee_version()} (scripts/dev-setup.sh installs it)")
        cls.lychee = found
        cls.server = StatusServer()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.close()

    def run_lychee(self, links: Dict[str, str]) -> Tuple[int, Dict[str, Any], str, str]:
        """Checks a Markdown file with these links (text: address) as scripts/verify.sh does, in a new folder. Returns lychee's exit status, its report, the cache it wrote and its messages."""
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "links.md").write_text("# Links\n\n" + "".join(f"- [{text}]({url})\n" for text, url in links.items()), encoding="utf-8")
            report = Path(folder) / "report.json"
            command = [
                {"lychee": self.lychee, "lychee.toml": str(ROOT / "lychee.toml"), "$report": str(report)}.get(word, word)
                for word in shlex.split(VERIFY_COMMAND)
            ]
            # Without proxies, so that only lychee's own answer counts (behind a proxy, the proxy answers for a name that does not resolve); and without a GitHub token, which lychee would use for github.com links.
            environment = {name: value for name, value in os.environ.items() if name.lower() not in ("http_proxy", "https_proxy", "all_proxy", "no_proxy", "github_token")}
            result = subprocess.run(command, input="links.md\n", cwd=folder, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300, check=False)
            cache_file = Path(folder) / ".lycheecache"
            cache = cache_file.read_text(encoding="utf-8") if cache_file.exists() else ""
            data = json.loads(report.read_text(encoding="utf-8")) if report.exists() and report.stat().st_size else {}
            return result.returncode, data, cache, result.stderr

    def answers(self, report: Dict[str, Any], key: str) -> Dict[str, Any]:
        return {body["url"]: body["status"].get("code") for body in report.get(key, {}).get("links.md", [])}

    def test_rate_limits_and_temporary_server_errors_pass(self) -> None:
        links = {"page": self.server.url(200), "rate limited": self.server.url(429), "unavailable": self.server.url(503), "gateway timeout": self.server.url(504)}
        status, report, _, messages = self.run_lychee(links)
        self.assertEqual(status, 0, messages)
        self.assertEqual(self.answers(report, "success_map"), {self.server.url(code): code for code in (200, 429, 503, 504)})
        self.assertEqual(report["error_map"], {})

    def test_answers_that_are_not_a_success_are_not_cached(self) -> None:
        _, _, cache, _ = self.run_lychee({"page": self.server.url(200), "rate limited": self.server.url(429), "unavailable": self.server.url(503), "gateway timeout": self.server.url(504)})
        cached = [line.split(",")[0] for line in cache.splitlines()]
        self.assertEqual(cached, [self.server.url(200)], "only the successful answer may be kept, so that the others are checked again next time")

    def test_broken_links_still_fail(self) -> None:
        broken = {
            "404 Not Found": self.server.url(404),
            "410 Gone": self.server.url(410),
            "500 Internal Server Error": self.server.url(500),
            "502 Bad Gateway": self.server.url(502),
            "a name that does not resolve": UNRESOLVABLE,
            "a refused connection": f"http://127.0.0.1:{unused_port()}/page",
        }
        for what, url in broken.items():
            with self.subTest(what):
                if url == UNRESOLVABLE and resolves(UNRESOLVABLE):
                    self.skipTest("this machine's DNS server answers for names that do not exist, so a failed lookup cannot be tested here")
                status, report, cache, messages = self.run_lychee({"page": self.server.url(200), what: url})
                self.assertEqual(status, 2, messages)
                self.assertEqual(list(self.answers(report, "error_map")), [url])
                self.assertNotIn(url, cache)

    def test_the_report_lists_the_accepted_answers(self) -> None:
        _, report, _, _ = self.run_lychee({"page": self.server.url(200), "unavailable": self.server.url(503), "gateway timeout": self.server.url(504)})
        lines = link_report.describe(report)
        self.assertIn(f"[503] {self.server.url(503)} (at 4:3) | 503 Service Unavailable", lines)
        self.assertIn(f"[504] {self.server.url(504)} (at 5:3) | 504 Gateway Timeout", lines)
        self.assertNotIn(f"[200] {self.server.url(200)} (at 3:3) | 200 OK", lines)


def response(url: str, text: str, code: Optional[int] = None, details: Optional[str] = None, line: int = 1, column: int = 1) -> Dict[str, Any]:
    """One response as lychee 0.24.2 writes it in its JSON report."""
    status: Dict[str, Any] = {"text": text}
    if code is not None:
        status["code"] = code
    if details is not None:
        status["details"] = details
    return {"url": url, "status": status, "span": {"line": line, "column": column}, "duration": {"secs": 0, "nanos": 1000}}


def report(success_map: Optional[Dict[str, Any]] = None, error_map: Optional[Dict[str, Any]] = None, timeout_map: Optional[Dict[str, Any]] = None, **counts: int) -> Dict[str, Any]:
    """A report as lychee 0.24.2 writes it with --verbose: the counts, and the responses grouped by file in success_map, error_map and timeout_map."""
    data: Dict[str, Any] = {"total": 0, "unique": 0, "successful": 0, "unknown": 0, "unsupported": 0, "timeouts": 0, "redirects": 0, "remaps": 0, "excludes": 0, "errors": 0, "cached": 0}
    data.update(counts)
    data.update({"success_map": success_map or {}, "error_map": error_map or {}, "timeout_map": timeout_map or {}, "suggestion_map": {}, "redirect_map": {}, "excluded_map": {}, "duration": {"secs": 1, "nanos": 0}, "detailed_stats": True})
    return data


class LinkReportTests(unittest.TestCase):
    """scripts/link-report.py, with reports shaped like those of lychee 0.24.2."""

    def run_script(self, content: Optional[str]) -> Tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            if content is not None:
                path.write_text(content, encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = link_report.main([str(path)])
            return status, out.getvalue(), err.getvalue()

    def test_it_lists_failures_timeouts_and_accepted_answers_by_file(self) -> None:
        data = report(
            success_map={
                "b.md": [response("https://github.com/x", "503 Service Unavailable", 503, line=7, column=2), response("https://ok.test/", "200 OK", 200)],
                "a.md": [response("https://busy.test/", "429 Too Many Requests", 429, line=2, column=5), response("https://cached.test/", "OK (cached)", 200)],
            },
            error_map={
                "b.md": [
                    response("https://gone.test/", "Rejected status code: 404 Not Found", 404, line=9, column=1),
                    response("https://refused.test/", "Network error: Connection refused (…)", details="Connection refused - server may be down or port blocked", line=3, column=4),
                ]
            },
            timeout_map={"a.md": [response("https://slow.test/", "Timeout", details="Request timed out", line=4, column=1)]},
            total=7,
            unique=7,
            successful=4,
            errors=2,
            timeouts=1,
            excludes=12,
            cached=1,
        )
        status, out, err = self.run_script(json.dumps(data))
        self.assertEqual((status, err), (0, ""))
        self.assertEqual(
            out.splitlines(),
            [
                "Links that failed:",
                "[b.md]:",
                "[ERROR] https://refused.test/ (at 3:4) | Connection refused - server may be down or port blocked",
                "[404] https://gone.test/ (at 9:1) | Rejected status code: 404 Not Found",
                "",
                "Timed out, which does not fail the check (accept_timeouts in lychee.toml); checked again next time:",
                "[a.md]:",
                "[TIMEOUT] https://slow.test/ (at 4:1) | Request timed out",
                "",
                "Accepted although the answer was not a success (accept in lychee.toml: the site was limiting automated checks, or was temporarily unable to answer); not cached, so checked again next time:",
                "[a.md]:",
                "[429] https://busy.test/ (at 2:5) | 429 Too Many Requests",
                "[b.md]:",
                "[503] https://github.com/x (at 7:2) | 503 Service Unavailable",
                "",
                "7 links (7 different): 4 OK (2 of them accepted without a success answer), 2 failed, 1 timed out, 12 skipped (not http or https, or excluded in lychee.toml), 1 reused from lychee's cache (this run's or the last day's).",
            ],
        )

    def test_when_every_link_works_it_prints_only_the_summary(self) -> None:
        status, out, _ = self.run_script(json.dumps(report(success_map={"a.md": [response("https://ok.test/", "200 OK", 200)]}, total=1, unique=1, successful=1)))
        self.assertEqual(status, 0)
        self.assertEqual(out.splitlines(), ["1 links (1 different): 1 OK (0 of them accepted without a success answer), 0 failed, 0 timed out, 0 skipped (not http or https, or excluded in lychee.toml), 0 reused from lychee's cache (this run's or the last day's)."])

    def test_it_refuses_a_report_that_leaves_out_the_links_that_passed(self) -> None:
        data = report()
        data["detailed_stats"] = False
        status, out, err = self.run_script(json.dumps(data))
        self.assertEqual((status, out), (2, ""))
        self.assertIn("lychee must run with --verbose", err)

    def test_it_refuses_a_missing_or_broken_report(self) -> None:
        broken_shape = report()
        broken_shape["success_map"] = []
        for what, content in {"no file": None, "an empty file": "", "not JSON": "{", "not an object": "[]", "a map that is not one": json.dumps(broken_shape)}.items():
            with self.subTest(what):
                status, out, err = self.run_script(content)
                self.assertEqual((status, out), (2, ""))
                self.assertTrue(err.startswith("link-report.py: "), err)

    def test_control_characters_are_written_out(self) -> None:
        sneaky = "https://example.test/\r::error::forged"
        status, out, _ = self.run_script(json.dumps(report(error_map={"a.md\n::warning::x": [response(sneaky, "Rejected status code: 404 Not Found", 404)]}, total=1, unique=1, errors=1)))
        self.assertEqual(status, 0)
        self.assertNotIn("\r", out)
        self.assertFalse(any(line.startswith("::") for line in out.splitlines()), out)
        self.assertIn("[404] https://example.test/\\r::error::forged (at 1:1)", out)
        self.assertIn("[a.md\\n::warning::x]:", out)


if __name__ == "__main__":
    unittest.main()
