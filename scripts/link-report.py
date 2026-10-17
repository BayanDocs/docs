#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Prints the result of the external-link check of scripts/verify.sh from the JSON report that lychee writes (lychee --verbose --format json --output FILE).
#
# lychee decides which links fail, with the rules in lychee.toml, and verify.sh takes its exit status as the result; this script only shows what lychee found. It exists because lychee's own summary leaves out the answers that lychee.toml accepts although they are not a success: "429 Too Many Requests", "500 Internal Server Error", "503 Service Unavailable" and "504 Gateway Timeout" (lychee counts them as OK). Listing every such link on every run keeps a site that stays unavailable from going unnoticed. Those answers are never cached (cache_exclude_status in lychee.toml), so each of these links is checked again on the next run.
#
# Usage: python3 scripts/link-report.py REPORT
# Exit status: 0 when the report was read and printed, 2 when it could not be read (then verify.sh shows lychee's own messages).
# Needs Python 3.9 or later and nothing outside its standard library. The tests are in scripts/tests/test_link_check.py.

from __future__ import annotations

import json
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


class ReportError(Exception):
    """The report is missing, is not JSON, or is not shaped like the report of lychee 0.24.2."""


@dataclass(frozen=True)
class Result:
    source: str  # the file the link is in, as given to lychee
    url: str
    label: str  # the status code, or TIMEOUT or ERROR when there is none
    message: str
    line: Optional[int]
    column: Optional[int]

    def sort_key(self) -> tuple:
        return (self.source, self.line or 0, self.column or 0, self.url)

    def __str__(self) -> str:
        where = f" (at {self.line}:{self.column})" if self.line is not None else ""
        return f"[{self.label}] {self.url}{where} | {self.message}"


def visible(text: str) -> str:
    """Text from a report with every control character (Unicode category Cc, such as a carriage return or the escape character of terminal colour codes) and every line or paragraph separator written out as an escape such as "\\r", so that a link can never start a line of its own in CI's log, where a line beginning with "::" would be read as a workflow command."""
    return "".join(repr(char)[1:-1] if unicodedata.category(char) in ("Cc", "Zl", "Zp") else char for char in text)


def _number(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _results(report: Dict[str, Any], key: str, fallback_label: str) -> List[Result]:
    """The responses in one of the report's maps ({source: [response, …]}), sorted by file, position and link."""
    responses = report.get(key)
    if not isinstance(responses, dict):
        raise ReportError(f"the report has no {key}")
    results = []
    for source, bodies in responses.items():
        if not isinstance(bodies, list):
            raise ReportError(f"{key} of {source!r} is not a list")
        for body in bodies:
            if not isinstance(body, dict) or not isinstance(body.get("url"), str) or not isinstance(body.get("status"), dict):
                raise ReportError(f"{key} of {source!r} holds a response without a url or a status")
            status = body["status"]
            code = _number(status.get("code"))
            span = body.get("span") if isinstance(body.get("span"), dict) else {}
            results.append(
                Result(
                    source=str(source),
                    url=body["url"],
                    label=str(code) if code is not None else fallback_label,
                    message=str(status.get("details") or status.get("text") or ""),
                    line=_number(span.get("line")),
                    column=_number(span.get("column")),
                )
            )
    return sorted(results, key=Result.sort_key)


def is_success_code(label: str) -> bool:
    return label.isdigit() and 200 <= int(label) <= 299


def load(path: Path) -> Dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ReportError(f"cannot read {path}: {error.strerror}") from None
    except ValueError as error:
        raise ReportError(f"{path} is not JSON ({error})") from None
    if not isinstance(report, dict):
        raise ReportError(f"{path} is not a lychee report")
    # Without --verbose, lychee leaves the links that passed out of its report, accepted answers included, and they would disappear from the output without a trace.
    if report.get("detailed_stats") is not True:
        raise ReportError(f"{path} lists no links that passed: lychee must run with --verbose")
    return report


def grouped(title: str, results: Sequence[Result]) -> List[str]:
    """A titled section with the results grouped by file, like lychee's own summary."""
    if not results:
        return []
    lines = [title]
    source = None
    for result in results:
        if result.source != source:
            source = result.source
            lines.append(f"[{source}]:")
        lines.append(str(result))
    lines.append("")
    return lines


def describe(report: Dict[str, Any]) -> List[str]:
    failed = _results(report, "error_map", "ERROR")
    timed_out = _results(report, "timeout_map", "TIMEOUT")
    accepted = [result for result in _results(report, "success_map", "OK") if not is_success_code(result.label)]
    lines: List[str] = []
    lines += grouped("Links that failed:", failed)
    lines += grouped("Timed out, which does not fail the check (accept_timeouts in lychee.toml); checked again next time:", timed_out)
    lines += grouped("Accepted although the answer was not a success (accept in lychee.toml: the site was limiting automated checks, or was temporarily unable to answer); not cached, so checked again next time:", accepted)
    counts = {key: _number(report.get(key)) or 0 for key in ("total", "unique", "successful", "errors", "timeouts", "excludes", "cached", "unknown", "unsupported")}
    summary = (
        f"{counts['total']} links ({counts['unique']} different): {counts['successful']} OK ({len(accepted)} of them accepted without a success answer), "
        f"{counts['errors']} failed, {counts['timeouts']} timed out, {counts['excludes']} skipped (not http or https, or excluded in lychee.toml), {counts['cached']} reused from lychee's cache (this run's or the last day's)"
    )
    if counts["unknown"] or counts["unsupported"]:
        summary += f", {counts['unknown']} unknown, {counts['unsupported']} unsupported"
    lines.append(summary + ".")
    return [visible(line) for line in lines]


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: link-report.py REPORT", file=sys.stderr)
        return 2
    try:
        lines = describe(load(Path(args[0])))
    except ReportError as error:
        print(visible(f"link-report.py: {error}"), file=sys.stderr)
        return 2
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
