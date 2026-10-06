#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Checks and applies the GitHub settings baseline of the BayanDocs organization: the organization's member privileges and GitHub Actions policy, the security configuration that new repositories start with, the teams that give people access, and each repository's merge settings, security features, immutable releases and rulesets. These are items 3–6 of the owner checklist (plan/09-owner-checklist.md); developer/github-settings.md explains every choice, the token the script needs and how to run it.
#
# Why a script: settings changed by clicking drift apart and leave no record. Written down here, every change is reviewed in a pull request, the same rules reach every repository, and `audit` shows at any time where GitHub differs from them.
#
# Usage: python3 scripts/github-settings.py audit|apply [--repo NAME]... [--yes]
#   audit         read-only: reports every setting as ok, DRIFT (differs from the baseline) or ERROR (could not be checked). Exit status 0 when everything matches, 1 when something differs, 2 when something could not be checked.
#   apply         lists the changes that would make GitHub match the baseline, asks you to type "apply" (unless --yes), makes them one at a time, then audits again.
#   --repo NAME   check only this repository (repeatable); the organization's own settings are always checked.
#
# The token, a fine-grained personal access token for the BayanDocs organization (its permissions are in developer/github-settings.md), is read from GH_TOKEN or GITHUB_TOKEN, or asked for without echoing it. It is sent only to https://api.github.com, never printed and never written anywhere. Needs Python 3.9 or later and nothing outside its standard library.

from __future__ import annotations

import argparse
import functools
import getpass
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# The baseline. Change it here, in a pull request, then run `apply`.
# developer/github-settings.md explains each choice in plain language.
# ---------------------------------------------------------------------------

ORG = "BayanDocs"

# The checks that every repository runs on every pull request, from identical workflows (X-001): DCO enforces the Developer Certificate of Origin rules of ADR-0003 (people sign off their own commits; the person who submits an agent's pull request signs off in its description), and REUSE lint keeps the licensing information complete. DCO stays red on an agent's pull request until its submitter adds their sign-off, so requiring it means no agent work is merged without one.
COMMON_CHECKS: List[str] = ["DCO", "REUSE lint"]

# The repositories this script manages, each with the CI checks that must pass before a pull request can merge into main. A check is named after its CI job as GitHub shows it on a pull request; a matrix job carries its matrix value in parentheses. List only jobs that run on every pull request (a job skipped by a path filter would block merging forever). When a job is renamed or added, update its list here and run `apply`.
REPOSITORIES: Dict[str, List[str]] = {
    "docs": ["scripts/verify.sh", *COMMON_CHECKS],
    "bayan-core": ["verify (ubuntu-24.04)", "verify (windows-latest)", "verify (macos-latest)", *COMMON_CHECKS],
    "bayan-web": ["pnpm verify (ubuntu-24.04)", "pnpm verify (macos-15)", "pnpm verify (macos-26-intel)", *COMMON_CHECKS],
    "bayan-desktop": [
        "Linux · verification gate",
        "Linux · AddressSanitizer and UndefinedBehaviorSanitizer",
        "macOS (arm64) · build and test",
        "Windows (MSVC) · build and test",
        *COMMON_CHECKS,
    ],
    "bayan-server": ["Verification gate", "PostgreSQL integration", "Container image", *COMMON_CHECKS],
}

# Organization member privileges (organization settings → Member privileges), as (API field, description, baseline value). Base permission "none": being a member gives no access to any repository by itself, so access comes only from the teams below, and a future private repository (such as the private corpus) is not readable by every member. Only owners create repositories and publish GitHub Pages sites. Deploy keys (per-repository SSH keys that bypass people's accounts) are switched off.
ORG_SETTINGS: List[Tuple[str, str, Any]] = [
    ("default_repository_permission", "Base permission of members", "none"),
    ("members_can_create_repositories", "Members can create repositories", False),
    ("members_can_create_public_repositories", "Members can create public repositories", False),
    ("members_can_create_private_repositories", "Members can create private repositories", False),
    ("members_can_fork_private_repositories", "Members can fork private repositories", False),
    ("members_can_create_pages", "Members can publish GitHub Pages sites", False),
    ("members_can_create_public_pages", "Members can publish public GitHub Pages sites", False),
    ("members_can_create_private_pages", "Members can publish private GitHub Pages sites", False),
    ("deploy_keys_enabled_for_repositories", "Deploy keys allowed", False),
    # GitHub signs off every commit made in its web interface (an edit, an accepted review suggestion) in the name of the person committing, so it passes the DCO check (X-001 follow-up 2). It applies to the web interface only: commits made with Git or through the API, as agents make them, are never signed off for anyone (ADR-0003: only a person certifies the DCO).
    ("web_commit_signoff_required", "Commits made in the web interface are signed off", True),
]

# Organization settings that GitHub's API can read but not change, as (API field, description, baseline value, where to change it). `audit` checks them; `apply` cannot fix them.
ORG_SETTINGS_BY_HAND: List[Tuple[str, str, Any, str]] = [
    (
        "two_factor_requirement_enabled",
        "Two-factor authentication required for everyone",
        True,
        "organization settings → Authentication security → Require two-factor authentication",
    ),
]

# Settings that GitHub's API can neither read nor change. Every audit lists them at the end; check each once in the web interface.
REMINDERS: List[str] = [
    "Personal access tokens: require administrator approval for fine-grained tokens and restrict access by classic tokens (organization settings → Personal access tokens → Settings).",
    "Third-party OAuth applications stay restricted (organization settings → OAuth application policy).",
    "Member privileges: only owners may change repository visibility, delete or transfer repositories, delete issues, and invite outside collaborators (organization settings → Member privileges).",
]

# GitHub Actions policy for every repository of the organization (organization settings → Actions → General). Repositories cannot loosen it.
ACTIONS_PERMISSIONS: List[Tuple[str, str, Any]] = [
    ("enabled_repositories", "Actions enabled for", "all"),
    ("allowed_actions", "Actions allowed", "selected"),  # only the actions listed below
    ("sha_pinning_required", "Actions must be pinned to a full commit SHA", True),  # ADR-0017
]
ACTIONS_ALLOWED: List[Tuple[str, str, Any]] = [
    ("github_owned_allowed", "GitHub's own actions allowed", True),  # actions/* and github/*
    ("verified_allowed", "Marketplace 'verified creator' actions allowed", False),  # no blanket trust
    # Third-party actions, one "owner/repository@*" pattern each. Any commit of an allowed action may be used, because the SHA pin in each workflow is what reviewers check. Keep the list sorted. X-002 proposes additions (for example OpenSSF Scorecard); until a pattern is added here and applied, a workflow that uses that action fails.
    ("patterns_allowed", "Third-party actions allowed", []),
]
ACTIONS_WORKFLOW: List[Tuple[str, str, Any]] = [
    ("default_workflow_permissions", "Default GITHUB_TOKEN permission", "read"),  # workflows ask for more per job
    ("can_approve_pull_request_reviews", "Actions can create and approve pull requests", False),
]
# Workflows triggered by pull requests from forks of public repositories wait for a maintainer's approval, for every outside contributor (not only first-time ones).
ACTIONS_FORK_APPROVAL: List[Tuple[str, str, Any]] = [
    ("approval_policy", "Approval of fork pull request workflows", "all_external_contributors"),
]
# Pull requests from forks of private repositories never run workflows. There are no private repositories yet; the private corpus (owner checklist item 10) may become one.
ACTIONS_PRIVATE_FORKS: List[Tuple[str, str, Any]] = [
    ("run_workflows_from_fork_pull_requests", "Workflows run on pull requests from forks of private repositories", False),
]

# Immutable releases in every repository of the organization, including ones created later (owner checklist item 6): once a release is published, its tag and files cannot be changed.
IMMUTABLE_RELEASES: List[Tuple[str, str, Any]] = [
    ("enforced_repositories", "Immutable releases enforced for", "all"),
]

# The security configuration that new repositories get automatically (organization settings → Advanced Security → Configurations), so a repository created later starts with the same protection. Existing repositories are set directly below instead, so that each setting can be checked and fixed on its own. Dependabot opens no pull requests: alerts only (ADR-0017).
SECURITY_CONFIGURATION_NAME = "BayanDocs baseline"
SECURITY_CONFIGURATION: List[Tuple[str, str, Any]] = [
    ("description", "Description", "Alerts only, no update pull requests (ADR-0017). Managed by scripts/github-settings.py in BayanDocs/docs."),
    ("dependency_graph", "Dependency graph", "enabled"),
    ("dependency_graph_autosubmit_action", "Automatic dependency submission", "disabled"),
    ("dependabot_alerts", "Dependabot alerts", "enabled"),
    ("dependabot_security_updates", "Dependabot security update pull requests", "disabled"),
    ("code_scanning_default_setup", "Code scanning default setup", "disabled"),  # X-002 adds CodeQL as workflows instead
    ("secret_scanning", "Secret scanning", "enabled"),
    ("secret_scanning_push_protection", "Push protection", "enabled"),
    ("private_vulnerability_reporting", "Private vulnerability reporting", "enabled"),
    ("enforcement", "Enforcement (repositories cannot override it)", "enforced"),
]
# The product that the secret scanning features above belong to (free for public repositories). It is sent with every change of the configuration, but GitHub does not return it, so it cannot be audited.
SECURITY_CONFIGURATION_PRODUCTS: Dict[str, str] = {"secret_protection": "enabled"}
# Which new repositories get the configuration: "public", "private_and_internal", "all" or "none". Only public ones: on private repositories, secret scanning and push protection are paid features.
SECURITY_CONFIGURATION_DEFAULT_FOR = "public"


@dataclass(frozen=True)
class Team:
    name: str
    slug: str  # the name GitHub derives for URLs and the API
    description: str
    permission: str  # role in every managed repository: pull, triage, push, maintain or admin


# Teams are the only way people get access (base permission is "none"). Both start empty; add people in the web interface (organization → Teams). Maintainers can merge pull requests and manage issues and releases but cannot change settings; triagers can label, assign and close issues and pull requests but cannot push.
TEAMS: List[Team] = [
    Team("Maintainers", "maintainers", "Review and merge pull requests, manage issues and releases. No access to settings.", "maintain"),
    Team("Triage", "triage", "Label, assign and close issues and pull requests. No write access.", "triage"),
]

# Merge settings of every managed repository (repository settings → General). Squash merging only: each pull request becomes one commit on main, titled with the pull request's title (a Conventional Commit), and GitHub fills in the pull request's description as its message. The description is the hand-off, and it carries the submitter's Signed-off-by line, which the DCO check has verified, so the sign-off reaches the commit on main as ADR-0003 asks without anyone pasting it in (X-001 follow-up 10). The messages of the individual commits are not kept.
REPOSITORY_SETTINGS: List[Tuple[str, str, Any]] = [
    ("default_branch", "Default branch", "main"),
    ("allow_squash_merge", "Squash merging allowed", True),
    ("allow_merge_commit", "Merge commits allowed", False),
    ("allow_rebase_merge", "Rebase merging allowed", False),
    ("squash_merge_commit_title", "Squash commit title", "PR_TITLE"),
    ("squash_merge_commit_message", "Squash commit message", "PR_BODY"),
    ("allow_auto_merge", "Auto-merge allowed", False),
    ("allow_update_branch", "Offer to update pull request branches", True),
    ("delete_branch_on_merge", "Delete branches after merging", True),
    ("has_wiki", "Wiki enabled", False),  # documentation lives in the docs repository, where it is reviewed
    ("web_commit_signoff_required", "Commits made in the web interface are signed off", True),  # also set organization-wide above
]

# Secret scanning in every managed repository (repository settings → Advanced Security): find committed credentials, and block pushes that contain known secret formats.
SECRET_SCANNING: List[Tuple[str, str, Any]] = [
    ("secret_scanning", "Secret scanning", "enabled"),
    ("secret_scanning_push_protection", "Push protection", "enabled"),
]

# The app ID of GitHub Actions. Required checks must come from it, so that nobody can satisfy a check by posting a passing commit status with the same name from somewhere else. GitHub's documentation does not state the number, so every audit looks it up (GET /apps/github-actions), and no rule naming it is applied unless the two agree: a wrong ID would make every pull request wait forever.
GITHUB_ACTIONS_APP_ID = 15368


def main_branch_ruleset(required_checks: List[str]) -> Dict[str, Any]:
    """The ruleset that protects main (owner checklist item 3).

    Every change reaches main through a pull request that is squash-merged by GitHub (so every commit on main is one that GitHub created and signed), after all review conversations are resolved and the required checks have passed on a branch that is up to date with main. Nobody can push directly, force-push or delete main, and nobody can bypass the rules: changing them means changing this baseline, in a pull request. No approving review is required while the owner is the only maintainer, because GitHub does not let anyone approve their own pull request and agents open pull requests as the owner; raise required_approving_review_count when a second maintainer joins. Signed commits are not required: GitHub can refuse to squash-merge a pull request whose own commits lack a verified signature, which would shut out contributors who do not sign, and main already holds only commits signed by GitHub.
    """
    rules: List[Dict[str, Any]] = [
        {"type": "deletion"},
        {"type": "non_fast_forward"},
        {"type": "required_linear_history"},
        {
            "type": "pull_request",
            "parameters": {
                "allowed_merge_methods": ["squash"],
                "dismiss_stale_reviews_on_push": True,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_approving_review_count": 0,
                "required_review_thread_resolution": True,
            },
        },
    ]
    if required_checks:
        rules.append(
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [
                        {"context": check, "integration_id": GITHUB_ACTIONS_APP_ID} for check in required_checks
                    ],
                    "strict_required_status_checks_policy": True,
                },
            }
        )
    return {
        "name": "Protect main",
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": rules,
    }


def release_tag_ruleset() -> Dict[str, Any]:
    """Release tags (v1.2.3) can be created but never moved or deleted, so a version always names the same code. Immutable releases protect a tag once its release is published; this also covers tags without a release."""
    return {
        "name": "Protect release tags",
        "target": "tag",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["refs/tags/v*"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "update", "parameters": {"update_allows_fetch_and_merge": False}},
        ],
    }


# ---------------------------------------------------------------------------
# Talking to GitHub
# ---------------------------------------------------------------------------

API = "https://api.github.com"
# The REST API version whose documentation this script follows. The previous version, 2022-11-28, is supported until 2028-03-10; check GitHub's list of breaking changes before moving to a newer one.
API_VERSION = "2026-03-10"
USER_AGENT = "BayanDocs-github-settings"
WRITE_INTERVAL = 1.0  # seconds between changes: GitHub asks clients that make many changes to wait at least one second between them
MAX_RATE_LIMIT_WAIT = 900.0  # give up rather than wait longer than this for a rate limit to reset

# A transport sends one request and returns (status, headers with lower-case names, body). Tests replace it with a fake GitHub.
Transport = Callable[[str, str, Dict[str, str], Optional[bytes]], Tuple[int, Dict[str, str], bytes]]


class ApiError(Exception):
    """GitHub answered with a status the script did not expect."""

    def __init__(self, method: str, path: str, status: int, message: str) -> None:
        super().__init__(f"{method} {path} failed with HTTP {status}: {message}")
        self.status = status


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    """Turn every redirect into an error, so the token is never sent anywhere else."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def urllib_transport(method: str, url: str, headers: Dict[str, str], body: Optional[bytes]) -> Tuple[int, Dict[str, str], bytes]:
    request = urllib.request.Request(url, data=body, method=method)
    for name, value in headers.items():
        # "Unredirected" headers are never copied onto a redirected request; redirects are refused anyway.
        request.add_unredirected_header(name, value)
    opener = urllib.request.build_opener(_NoRedirects)
    try:
        with opener.open(request, timeout=60) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in error.headers.items()}, error.read()


@dataclass
class Response:
    status: int
    headers: Dict[str, str]
    data: Any


class GitHub:
    """A minimal client for GitHub's REST API that sends the token only to api.github.com."""

    def __init__(
        self,
        token: str,
        transport: Transport = urllib_transport,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._token = token
        self._transport = transport
        self._sleep = sleep
        self._clock = clock
        self._last_write: Optional[float] = None
        self.token_expiry: Optional[str] = None
        self.writes = 0

    def __repr__(self) -> str:  # never show the token, even in a traceback
        return "GitHub(api.github.com)"

    def request(self, method: str, path: str, body: Any = None, expect: Tuple[int, ...] = (200,)) -> Response:
        if not path.startswith("/"):
            raise ValueError(f"API paths start with '/': {path}")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": API_VERSION,
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        writing = method != "GET"
        attempt = 0
        while True:
            if writing:
                self._wait_between_writes()
            status, response_headers, raw = self._transport(method, API + path, headers, data)
            if writing:
                self._last_write = self._clock()
            wait = self._rate_limit_wait(status, response_headers, raw)
            if wait is None or attempt >= 3:
                break
            if wait > MAX_RATE_LIMIT_WAIT:
                raise ApiError(method, path, status, f"rate limited for another {int(wait)} seconds; run the script again later")
            self._sleep(wait)
            attempt += 1
        if writing:
            self.writes += 1
        if "github-authentication-token-expiration" in response_headers:
            self.token_expiry = response_headers["github-authentication-token-expiration"]
        data_out = _parse_json(raw)
        if status not in expect:
            raise ApiError(method, path, status, _error_message(data_out, raw))
        return Response(status, response_headers, data_out)

    def get(self, path: str) -> Any:
        return self.request("GET", path).data

    def put(self, path: str, body: Any = None) -> Any:
        return self.request("PUT", path, body, expect=(200, 201, 204)).data

    def patch(self, path: str, body: Any) -> Any:
        # Some endpoints answer 201 or 204 when nothing needed to change.
        return self.request("PATCH", path, body, expect=(200, 201, 204)).data

    def post(self, path: str, body: Any) -> Any:
        return self.request("POST", path, body, expect=(200, 201)).data

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path, expect=(204,)).data

    def paginate(self, path: str, key: Optional[str] = None) -> List[Any]:
        """Returns every item of a list endpoint, following GitHub's page links (which must stay on api.github.com)."""
        next_path: Optional[str] = path + ("&" if "?" in path else "?") + "per_page=100"
        items: List[Any] = []
        while next_path:
            response = self.request("GET", next_path)
            page = response.data[key] if key else response.data
            if not isinstance(page, list):
                raise ApiError("GET", next_path, response.status, "expected a list")
            items.extend(page)
            next_path = _next_page(response.headers.get("link", ""))
        return items

    def _wait_between_writes(self) -> None:
        if self._last_write is not None:
            remaining = WRITE_INTERVAL - (self._clock() - self._last_write)
            if remaining > 0:
                self._sleep(remaining)

    def _rate_limit_wait(self, status: int, headers: Dict[str, str], raw: bytes) -> Optional[float]:
        """Seconds to wait before retrying a rate-limited request, or None if it was not rate limited."""
        if status not in (403, 429):
            return None
        if "retry-after" in headers:
            return max(1.0, float(headers["retry-after"]))
        if headers.get("x-ratelimit-remaining") == "0" and "x-ratelimit-reset" in headers:
            return max(1.0, float(headers["x-ratelimit-reset"]) - self._clock() + 1.0)
        if b"secondary rate limit" in raw.lower():
            return 60.0
        return None


def _parse_json(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None


def _error_message(data: Any, raw: bytes) -> str:
    if isinstance(data, dict) and data.get("message"):
        message = str(data["message"])
        details = data.get("errors")
        if details:
            message += " " + json.dumps(details, ensure_ascii=False)
        return message
    return raw[:200].decode("utf-8", "replace") or "(no message)"


def _next_page(link_header: str) -> Optional[str]:
    """The path of the next page from a Link header, or None on the last page."""
    for part in link_header.split(","):
        url, _, params = part.partition(";")
        if 'rel="next"' not in params:
            continue
        url = url.strip().strip("<>")
        if not url.startswith(API + "/"):
            raise ValueError(f"refusing to follow a page link outside {API}: {url}")
        return url[len(API) :]
    return None


# ---------------------------------------------------------------------------
# Comparing GitHub with the baseline
# ---------------------------------------------------------------------------

OK, DRIFT, ERROR, INFO = "ok", "DRIFT", "ERROR", "info"


@dataclass
class Finding:
    state: str  # OK, DRIFT, ERROR or INFO
    scope: str  # "organization BayanDocs" or "repository docs"
    text: str


@dataclass
class Change:
    scope: str
    text: str
    run: Callable[[], Any]


def show(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


# Errors that one check or change can run into without the whole run having to stop: GitHub refusing a request, or an answer shaped differently than documented.
UNEXPECTED = (ApiError, KeyError, TypeError, ValueError, AttributeError)


def describe(error: Exception) -> str:
    if isinstance(error, ApiError):
        return str(error)
    return f"unexpected answer from GitHub ({type(error).__name__}: {error})"


# The repository roles that the API's "permission" values grant, as GitHub names them in role_name.
ROLE_NAMES = {"pull": "read", "triage": "triage", "push": "write", "maintain": "maintain", "admin": "admin"}


def _role(repository: Dict[str, Any]) -> Optional[str]:
    """A team's or person's role in a repository, from role_name or else from the permissions flags."""
    if repository.get("role_name"):
        return str(repository["role_name"])
    permissions = repository.get("permissions") or {}
    for flag, role in (("admin", "admin"), ("maintain", "maintain"), ("push", "write"), ("triage", "triage"), ("pull", "read")):
        if permissions.get(flag):
            return role
    return None


def _normalized(value: Any) -> Any:
    """Puts lists in a stable order, so that the order GitHub returns them in is not reported as a difference."""
    if isinstance(value, dict):
        return {key: _normalized(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return sorted((_normalized(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    return value


def ruleset_differences(have: Dict[str, Any], want: Dict[str, Any]) -> List[str]:
    """How a ruleset on GitHub differs from the baseline. Parameters that GitHub adds with default values, and that the baseline does not mention, are ignored."""
    differences = []
    for key in ("target", "enforcement"):
        if have.get(key) != want[key]:
            differences.append(f"{key} is {show(have.get(key))}, baseline {show(want[key])}")
    have_refs = (have.get("conditions") or {}).get("ref_name") or {}
    for key in ("include", "exclude"):
        if sorted(have_refs.get(key) or []) != sorted(want["conditions"]["ref_name"][key]):
            differences.append(f"branches or tags to {key} are {show(have_refs.get(key))}, baseline {show(want['conditions']['ref_name'][key])}")
    bypass = _normalized([{k: actor.get(k) for k in ("actor_id", "actor_type", "bypass_mode")} for actor in have.get("bypass_actors") or []])
    if bypass != _normalized(want["bypass_actors"]):
        differences.append(f"bypass list is {show(bypass)}, baseline {show(want['bypass_actors'])}")
    have_rules = {rule.get("type"): rule.get("parameters") or {} for rule in have.get("rules") or []}
    want_rules = {rule["type"]: rule.get("parameters") or {} for rule in want["rules"]}
    for rule_type in sorted(set(have_rules) - set(want_rules), key=str):
        differences.append(f"has the extra rule {rule_type}")
    for rule_type in sorted(set(want_rules) - set(have_rules)):
        differences.append(f"lacks the rule {rule_type}")
    for rule_type in sorted(set(want_rules) & set(have_rules)):
        for parameter, value in sorted(want_rules[rule_type].items()):
            current = have_rules[rule_type].get(parameter)
            if _normalized(current) != _normalized(value):
                differences.append(f"rule {rule_type}: {parameter} is {show(current)}, baseline {show(value)}")
    return differences


def _fields(drift: Dict[str, Any]) -> str:
    return ", ".join(f"{name}={show(value)}" for name, value in drift.items())


class Auditor:
    """Compares GitHub with the baseline. Collects findings for the report, and the changes that `apply` would make, in the order they must be made."""

    def __init__(self, gh: GitHub, repositories: Dict[str, List[str]]) -> None:
        self.gh = gh
        self.repositories = repositories
        self.findings: List[Finding] = []
        self.changes: List[Change] = []
        self.org_scope = f"organization {ORG}"
        self.org_enforces_immutable_releases = False
        self.actions_app_id_confirmed = False

    def add(self, state: str, scope: str, text: str) -> None:
        self.findings.append(Finding(state, scope, text))

    def plan(self, scope: str, text: str, function: Callable[..., Any], *args: Any) -> None:
        self.changes.append(Change(scope, text, functools.partial(function, *args)))

    def compare(self, scope: str, have: Any, wanted: List[Tuple[str, str, Any]], hint: str = "does the token lack a permission?") -> Dict[str, Any]:
        """Records one finding per setting; returns the settings that differ, with their baseline values."""
        drift: Dict[str, Any] = {}
        for name, label, want in wanted:
            if not isinstance(have, dict) or name not in have:
                self.add(ERROR, scope, f"{label}: GitHub's answer has no {name} ({hint})")
            elif _normalized(have[name]) == _normalized(want):
                self.add(OK, scope, f"{label}: {show(want)}")
            else:
                self.add(DRIFT, scope, f"{label}: {show(have[name])}, baseline {show(want)}")
                drift[name] = want
        return drift

    def section(self, scope: str, check: Callable[[], None]) -> None:
        """Runs one group of checks; if GitHub refuses a request or answers unexpectedly, the rest of the audit still runs."""
        try:
            check()
        except UNEXPECTED as error:
            self.add(ERROR, scope, describe(error))

    def run(self) -> None:
        self.check_identity()  # stops the audit if the token is rejected
        for check in (
            self.check_actions_app_id,
            self.check_organization,
            self.check_actions,
            self.check_immutable_releases,
            self.check_security_configuration,
            self.check_teams,
            self.check_people,
        ):
            self.section(self.org_scope, check)
        self.section(self.org_scope, self.check_repositories)

    # Organization ------------------------------------------------------------

    def check_identity(self) -> None:
        login = self.gh.get("/user")["login"]
        try:
            role = self.gh.get(f"/orgs/{ORG}/memberships/{login}").get("role")
        except ApiError as error:
            self.add(ERROR, self.org_scope, f"Could not read your membership: {error}")
            return
        if role == "admin":
            self.add(INFO, self.org_scope, f"Signed in as {login}, an owner of {ORG}")
        else:
            self.add(ERROR, self.org_scope, f"Signed in as {login}, whose role is {show(role)}: only owners can change these settings")

    def check_actions_app_id(self) -> None:
        app_id = self.gh.get("/apps/github-actions").get("id")
        if app_id == GITHUB_ACTIONS_APP_ID:
            self.actions_app_id_confirmed = True
            self.add(OK, self.org_scope, f"App ID of GitHub Actions, which required checks must come from: {app_id}")
        else:
            self.add(ERROR, self.org_scope, f"App ID of GitHub Actions is {show(app_id)}, but the baseline says {GITHUB_ACTIONS_APP_ID}: correct GITHUB_ACTIONS_APP_ID; until then no required checks are applied")

    def check_organization(self) -> None:
        scope = self.org_scope
        org = self.gh.get(f"/orgs/{ORG}")
        drift = self.compare(scope, org, ORG_SETTINGS)
        if drift:
            self.plan(scope, f"set member privileges ({_fields(drift)})", self.gh.patch, f"/orgs/{ORG}", drift)
        for name, label, want, where in ORG_SETTINGS_BY_HAND:
            if name not in org:
                self.add(ERROR, scope, f"{label}: GitHub's answer has no {name} (does the token lack a permission?)")
            elif org[name] == want:
                self.add(OK, scope, f"{label}: {show(want)}")
            else:
                self.add(DRIFT, scope, f"{label}: {show(org[name])}, baseline {show(want)}; the API cannot change this, use {where}")

    def check_actions(self) -> None:
        scope = self.org_scope
        base = f"/orgs/{ORG}/actions/permissions"
        permissions = self.gh.get(base)
        drift = self.compare(scope, permissions, ACTIONS_PERMISSIONS)
        if drift:
            # PUT replaces the whole policy, so it always sends every field.
            self.plan(scope, f"set the Actions policy ({_fields(drift)})", self.gh.put, base, {name: want for name, _, want in ACTIONS_PERMISSIONS})
        allowed_body = {name: want for name, _, want in ACTIONS_ALLOWED}
        if permissions.get("allowed_actions") == "selected":
            drift = self.compare(scope, self.gh.get(base + "/selected-actions"), ACTIONS_ALLOWED)
            if drift:
                self.plan(scope, f"set the list of allowed actions ({_fields(drift)})", self.gh.put, base + "/selected-actions", allowed_body)
        else:
            self.add(DRIFT, scope, "List of allowed actions: not in force, because allowed actions is not \"selected\"")
            self.plan(scope, f"set the list of allowed actions ({_fields(allowed_body)})", self.gh.put, base + "/selected-actions", allowed_body)
        drift = self.compare(scope, self.gh.get(base + "/workflow"), ACTIONS_WORKFLOW)
        if drift:
            self.plan(scope, f"set workflow permissions ({_fields(drift)})", self.gh.put, base + "/workflow", {name: want for name, _, want in ACTIONS_WORKFLOW})
        drift = self.compare(scope, self.gh.get(base + "/fork-pr-contributor-approval"), ACTIONS_FORK_APPROVAL)
        if drift:
            self.plan(scope, f"set approval of fork pull request workflows ({_fields(drift)})", self.gh.put, base + "/fork-pr-contributor-approval", drift)
        drift = self.compare(scope, self.gh.get(base + "/fork-pr-workflows-private-repos"), ACTIONS_PRIVATE_FORKS)
        if drift:
            self.plan(scope, f"set fork pull request workflows in private repositories ({_fields(drift)})", self.gh.put, base + "/fork-pr-workflows-private-repos", drift)

    def check_immutable_releases(self) -> None:
        scope = self.org_scope
        path = f"/orgs/{ORG}/settings/immutable-releases"
        drift = self.compare(scope, self.gh.get(path), IMMUTABLE_RELEASES)
        if drift:
            self.plan(scope, f"enforce immutable releases ({_fields(drift)})", self.gh.put, path, drift)
        # From here on the organization-wide setting covers every repository (now, or once the change above is made), so the repository checks only confirm it.
        self.org_enforces_immutable_releases = True

    def check_security_configuration(self) -> None:
        scope = self.org_scope
        base = f"/orgs/{ORG}/code-security/configurations"
        body = dict({name: want for name, _, want in SECURITY_CONFIGURATION}, **SECURITY_CONFIGURATION_PRODUCTS)
        label = f"Security configuration {show(SECURITY_CONFIGURATION_NAME)} for new repositories"
        found = [c for c in self.gh.paginate(base) if c.get("name") == SECURITY_CONFIGURATION_NAME]
        if not found:
            self.add(DRIFT, scope, f"{label}: missing")
            self.plan(scope, f"create the security configuration {show(SECURITY_CONFIGURATION_NAME)} and make it the default for new {SECURITY_CONFIGURATION_DEFAULT_FOR} repositories", self._create_security_configuration, dict(body, name=SECURITY_CONFIGURATION_NAME))
            return
        if len(found) > 1:
            self.add(ERROR, scope, f"{label}: {len(found)} configurations have this name; delete the extra ones in the web interface")
            return
        configuration = found[0]
        drift = self.compare(scope, configuration, [(name, f"{label}: {text}", want) for name, text, want in SECURITY_CONFIGURATION])
        if drift:
            self.plan(scope, f"update the security configuration ({_fields(drift)})", self.gh.patch, f"{base}/{configuration['id']}", dict(drift, **SECURITY_CONFIGURATION_PRODUCTS))
        defaults = self.gh.get(f"{base}/defaults")
        default_for = [entry.get("default_for_new_repos") for entry in defaults or [] if (entry.get("configuration") or {}).get("id") == configuration["id"]]
        if SECURITY_CONFIGURATION_DEFAULT_FOR in default_for:
            self.add(OK, scope, f"{label}: default for new {SECURITY_CONFIGURATION_DEFAULT_FOR} repositories")
        else:
            self.add(DRIFT, scope, f"{label}: not the default for new {SECURITY_CONFIGURATION_DEFAULT_FOR} repositories")
            self.plan(scope, f"make the security configuration the default for new {SECURITY_CONFIGURATION_DEFAULT_FOR} repositories", self.gh.put, f"{base}/{configuration['id']}/defaults", {"default_for_new_repos": SECURITY_CONFIGURATION_DEFAULT_FOR})

    def _create_security_configuration(self, body: Dict[str, Any]) -> None:
        created = self.gh.post(f"/orgs/{ORG}/code-security/configurations", body)
        self.gh.put(f"/orgs/{ORG}/code-security/configurations/{created['id']}/defaults", {"default_for_new_repos": SECURITY_CONFIGURATION_DEFAULT_FOR})

    def check_teams(self) -> None:
        scope = self.org_scope
        existing = {team["slug"]: team for team in self.gh.paginate(f"/orgs/{ORG}/teams")}
        for team in TEAMS:
            current = existing.pop(team.slug, None)
            if current is None:
                self.add(DRIFT, scope, f"Team {team.name}: missing")
                self.plan(scope, f"create the team {team.name}", self.gh.post, f"/orgs/{ORG}/teams", {"name": team.name, "description": team.description, "privacy": "closed"})
                for repo in self.repositories:
                    self.plan(scope, f"give the team {team.name} the {ROLE_NAMES[team.permission]} role in {repo}", self.gh.put, f"/orgs/{ORG}/teams/{team.slug}/repos/{ORG}/{repo}", {"permission": team.permission})
                continue
            drift = self.compare(scope, current, [("description", f"Team {team.name}: description", team.description), ("privacy", f"Team {team.name}: visibility", "closed")])
            if drift:
                self.plan(scope, f"update the team {team.name} ({_fields(drift)})", self.gh.patch, f"/orgs/{ORG}/teams/{team.slug}", drift)
            roles = {repo["name"]: _role(repo) for repo in self.gh.paginate(f"/orgs/{ORG}/teams/{team.slug}/repos")}
            for repo in self.repositories:
                want = ROLE_NAMES[team.permission]
                if roles.get(repo) == want:
                    self.add(OK, scope, f"Team {team.name}: {want} role in {repo}")
                else:
                    self.add(DRIFT, scope, f"Team {team.name}: role in {repo} is {show(roles.get(repo))}, baseline {show(want)}")
                    self.plan(scope, f"give the team {team.name} the {want} role in {repo}", self.gh.put, f"/orgs/{ORG}/teams/{team.slug}/repos/{ORG}/{repo}", {"permission": team.permission})
            for repo, role in sorted(roles.items()):
                if repo not in REPOSITORIES:
                    self.add(INFO, scope, f"Team {team.name} also has the {role} role in {repo}, which this script does not manage")
            members = sorted(member["login"] for member in self.gh.paginate(f"/orgs/{ORG}/teams/{team.slug}/members"))
            self.add(INFO, scope, f"Team {team.name} members: {', '.join(members) or 'none'}")
        for slug, team in sorted(existing.items()):
            self.add(INFO, scope, f"Team {team.get('name', slug)} is not part of the baseline; left as it is")

    def check_people(self) -> None:
        """Who has access: listed for review, never changed by the script."""
        scope = self.org_scope
        owners = sorted(member["login"] for member in self.gh.paginate(f"/orgs/{ORG}/members?role=admin"))
        members = sorted(member["login"] for member in self.gh.paginate(f"/orgs/{ORG}/members?role=member"))
        outside = sorted(person["login"] for person in self.gh.paginate(f"/orgs/{ORG}/outside_collaborators"))
        self.add(INFO, scope, f"Owners: {', '.join(owners) or 'none'}")
        self.add(INFO, scope, f"Members who are not owners: {', '.join(members) or 'none'}")
        self.add(INFO, scope, f"Outside collaborators: {', '.join(outside) or 'none'}")
        # Requiring two-factor authentication removes everyone in these lists from the organization.
        for kind, description in (("2fa_disabled", "without two-factor authentication"), ("2fa_insecure", "whose only second factor is insecure (such as SMS)")):
            people = sorted(person["login"] for path in ("members", "outside_collaborators") for person in self.gh.paginate(f"/orgs/{ORG}/{path}?filter={kind}"))
            self.add(INFO, scope, f"Members and outside collaborators {description}: {', '.join(people) or 'none'}")
        for app in self.gh.paginate(f"/orgs/{ORG}/installations", key="installations"):
            writes = sorted(name for name, level in (app.get("permissions") or {}).items() if level in ("write", "admin"))
            self.add(INFO, scope, f"Installed app {app.get('app_slug')}: {app.get('repository_selection')} repositories, can change {', '.join(writes) or 'nothing'}")

    # Repositories ------------------------------------------------------------

    def check_repositories(self) -> None:
        found = {repo["name"]: repo for repo in self.gh.paginate(f"/orgs/{ORG}/repos?type=all")}
        for name, repo in sorted(found.items()):
            if name in REPOSITORIES:
                continue
            if repo.get("archived"):
                self.add(INFO, self.org_scope, f"Repository {name} is archived; not checked")
            else:
                self.add(DRIFT, self.org_scope, f"Repository {name} is not in the baseline: add it to REPOSITORIES in scripts/github-settings.py (or archive it)")
        for name, checks in self.repositories.items():
            scope = f"repository {name}"
            if name not in found:
                self.add(ERROR, scope, "not found (renamed, deleted, or not visible to the token)")
                continue
            if found[name].get("archived"):
                self.add(INFO, scope, "archived; not checked")
                continue
            for check in (self.check_repository_settings, self.check_security_features, self.check_rulesets, self.check_access):
                self.section(scope, functools.partial(check, name, checks))

    def check_repository_settings(self, name: str, checks: List[str]) -> None:
        scope = f"repository {name}"
        path = f"/repos/{ORG}/{name}"
        repo = self.gh.get(path)
        self.add(INFO, scope, f"Visibility: {repo.get('visibility')}")
        drift = self.compare(scope, repo, REPOSITORY_SETTINGS, hint="GitHub shows merge settings only to tokens with the Contents permission, read and write")
        if "squash_merge_commit_title" in drift or "squash_merge_commit_message" in drift:
            # GitHub accepts the squash commit title and message only as a pair.
            drift.update({key: want for key, _, want in REPOSITORY_SETTINGS if key.startswith("squash_merge_commit_")})
        security = repo.get("security_and_analysis")
        if not isinstance(security, dict):
            self.add(ERROR, scope, "Secret scanning: GitHub's answer has no security_and_analysis (does the token lack the Administration permission?)")
        else:
            have = {key: (security.get(key) or {}).get("status") for key, _, _ in SECRET_SCANNING}
            scanning = self.compare(scope, have, SECRET_SCANNING)
            if scanning:
                drift["security_and_analysis"] = {key: {"status": value} for key, value in scanning.items()}
        if drift:
            self.plan(scope, f"update settings ({_fields(drift)})", self.gh.patch, path, drift)

    def _switch(self, scope: str, label: str, path: str, have: bool, want: bool, set_by: Optional[str] = None) -> None:
        if have == want:
            self.add(OK, scope, f"{label}: {show(want)}")
            return
        if set_by:
            # Changing it here would conflict with the organization-wide setting that controls it.
            self.add(DRIFT, scope, f"{label}: {show(have)}, baseline {show(want)}; set by {set_by}")
            return
        self.add(DRIFT, scope, f"{label}: {show(have)}, baseline {show(want)}")
        if want:
            self.plan(scope, f"turn on {label.lower()}", self.gh.put, path)
        else:
            self.plan(scope, f"turn off {label.lower()}", self.gh.delete, path)

    def check_security_features(self, name: str, checks: List[str]) -> None:
        scope = f"repository {name}"
        base = f"/repos/{ORG}/{name}"
        immutable_set_by = "the organization's immutable releases setting" if self.org_enforces_immutable_releases else None
        # (description, address, baseline, how to read it, organization setting that controls it); each is checked on its own, so one refusal hides nothing else.
        for label, path, want, read, set_by in (
            ("Dependabot alerts", f"{base}/vulnerability-alerts", True, self._on_if_204, None),
            ("Dependabot security update pull requests", f"{base}/automated-security-fixes", False, self._enabled_unless_404, None),
            ("Private vulnerability reporting", f"{base}/private-vulnerability-reporting", True, self._enabled_field, None),
            ("Immutable releases", f"{base}/immutable-releases", True, self._enabled_unless_404, immutable_set_by),
        ):
            self.section(scope, functools.partial(self._check_switch, scope, label, path, want, read, set_by))
        self.section(scope, functools.partial(self._check_attached_configuration, scope, f"{base}/code-security-configuration"))

    def _check_attached_configuration(self, scope: str, path: str) -> None:
        """An enforced security configuration attached to a repository silently overrides changes made to it directly, so the report shows which one is attached."""
        response = self.gh.request("GET", path, expect=(200, 204))
        if response.status == 204 or not response.data:
            self.add(INFO, scope, "Security configuration attached: none (settings are made directly)")
            return
        configuration = response.data.get("configuration") or {}
        self.add(INFO, scope, f"Security configuration attached: {show(configuration.get('name'))}, status {response.data.get('status')}; it takes precedence over the settings above where it is enforced")

    def _check_switch(self, scope: str, label: str, path: str, want: bool, read: Callable[[str], bool], set_by: Optional[str]) -> None:
        self._switch(scope, label, path, read(path), want, set_by)

    def _on_if_204(self, path: str) -> bool:
        """For endpoints that answer 204 when a feature is on and 404 when it is off."""
        return self.gh.request("GET", path, expect=(204, 404)).status == 204

    def _enabled_field(self, path: str) -> bool:
        """For endpoints that answer with {"enabled": true or false}."""
        return bool(self.gh.get(path)["enabled"])

    def _enabled_unless_404(self, path: str) -> bool:
        """For endpoints that answer {"enabled": ...} when a feature is on and 404 when it is off."""
        response = self.gh.request("GET", path, expect=(200, 404))
        return response.status == 200 and bool(response.data["enabled"])

    def check_rulesets(self, name: str, checks: List[str]) -> None:
        scope = f"repository {name}"
        base = f"/repos/{ORG}/{name}/rulesets"
        by_name: Dict[str, List[Dict[str, Any]]] = {}
        for ruleset in self.gh.paginate(base + "?includes_parents=false"):
            by_name.setdefault(ruleset.get("name", ""), []).append(ruleset)
        for want in (main_branch_ruleset(checks), release_tag_ruleset()):
            label = f"Ruleset {show(want['name'])}"
            matches = by_name.pop(want["name"], [])
            # A rule that names GitHub Actions by a wrong app ID would block every pull request, so it is applied only once the ID is confirmed.
            unsafe = not self.actions_app_id_confirmed and any(rule["type"] == "required_status_checks" for rule in want["rules"])
            if len(matches) > 1:
                self.add(ERROR, scope, f"{label}: {len(matches)} rulesets have this name; delete the extra ones (repository settings → Rules → Rulesets)")
                continue
            if not matches:
                self.add(DRIFT, scope, f"{label}: missing")
                change: Tuple[str, Callable[..., Any], Tuple[Any, ...]] = (f"create the ruleset {show(want['name'])}", self.gh.post, (base, want))
            else:
                differences = ruleset_differences(self.gh.get(f"{base}/{matches[0]['id']}"), want)
                if not differences:
                    self.add(OK, scope, f"{label}: matches the baseline ({len(want['rules'])} rules)")
                    continue
                for difference in differences:
                    self.add(DRIFT, scope, f"{label}: {difference}")
                change = (f"replace the rules of the ruleset {show(want['name'])}", self.gh.put, (f"{base}/{matches[0]['id']}", want))
            if unsafe:
                self.add(ERROR, scope, f"{label}: not changed, because the app ID of GitHub Actions is not confirmed (see the organization's report)")
            else:
                self.plan(scope, change[0], change[1], *change[2])
        for other, rulesets in sorted(by_name.items()):
            for ruleset in rulesets:
                self.add(INFO, scope, f"Ruleset {show(other)} ({ruleset.get('target')}, {ruleset.get('enforcement')}) is not part of the baseline; left as it is")

    def check_access(self, name: str, checks: List[str]) -> None:
        """Direct collaborators and deploy keys: listed for review, never changed by the script."""
        scope = f"repository {name}"
        base = f"/repos/{ORG}/{name}"
        people = sorted(f"{person['login']} ({_role(person)})" for person in self.gh.paginate(f"{base}/collaborators?affiliation=direct"))
        self.add(INFO, scope, f"People with direct access: {', '.join(people) or 'none'}")
        keys = sorted(f"{key.get('title')} ({'read-only' if key.get('read_only') else 'read-write'})" for key in self.gh.paginate(f"{base}/keys"))
        if keys:
            self.add(INFO, scope, f"Deploy keys: {', '.join(keys)}")


# ---------------------------------------------------------------------------
# Report, apply and the command line
# ---------------------------------------------------------------------------


def print_report(auditor: Auditor, out: Any) -> int:
    """Prints the findings grouped by organization and repository; returns the exit status."""
    scopes: Dict[str, List[Finding]] = {}
    for finding in auditor.findings:
        scopes.setdefault(finding.scope, []).append(finding)
    for scope, findings in scopes.items():
        print(f"\n{scope[0].upper()}{scope[1:]}", file=out)
        for finding in findings:
            print(f"  {finding.state:<5}  {finding.text}", file=out)
    if auditor.gh.token_expiry:
        print(f"\nThe token expires {auditor.gh.token_expiry}.", file=out)
    else:
        print("\nGitHub reported no expiry date for this token: delete it when you are done (github.com → Settings → Developer settings).", file=out)
    print("\nCheck these by hand once; GitHub's API can neither read nor change them:", file=out)
    for reminder in REMINDERS:
        print(f"  - {reminder}", file=out)
    counts = {state: sum(1 for f in auditor.findings if f.state == state) for state in (OK, DRIFT, ERROR)}
    print(f"\nSummary: {counts[OK]} ok, {counts[DRIFT]} differ from the baseline, {counts[ERROR]} could not be checked; {len(auditor.changes)} change(s) planned.", file=out)
    if counts[ERROR]:
        return 2
    return 1 if counts[DRIFT] else 0


def apply_changes(auditor: Auditor, assume_yes: bool, out: Any, ask: Callable[[str], str]) -> Optional[int]:
    """Makes the planned changes. Returns the number that failed, or None if the user declined."""
    changes = auditor.changes
    if not changes:
        print("\nNothing to change that the API can set.", file=out)
        return 0
    print(f"\nChanges to make in {ORG}, in this order:", file=out)
    for number, change in enumerate(changes, 1):
        print(f"  {number:>2}. {change.scope}: {change.text}", file=out)
    if not assume_yes:
        out.flush()
        try:
            answer = ask(f'\nType "apply" to make these {len(changes)} changes: ')
        except EOFError:
            answer = ""
        if answer.strip() != "apply":
            print("Nothing was changed.", file=out)
            return None
    failed = 0
    for number, change in enumerate(changes, 1):
        try:
            change.run()
            print(f"  {number:>2}. done: {change.scope}: {change.text}", file=out)
        except UNEXPECTED as error:
            failed += 1
            print(f"  {number:>2}. FAILED: {change.scope}: {change.text}: {describe(error)}", file=out)
    return failed


def token_kind(token: str) -> str:
    for prefix, kind in (
        ("github_pat_", "fine-grained personal access token"),
        ("ghp_", "classic personal access token"),
        ("gho_", "OAuth token (such as the GitHub CLI's)"),
    ):
        if token.startswith(prefix):
            return kind
    return "token of an unknown kind"


def read_token(ask_hidden: Callable[[str], str] = getpass.getpass) -> str:
    for variable in ("GH_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(variable, "").strip()
        if token:
            return token
    if sys.stdin.isatty():
        token = ask_hidden("GitHub token for BayanDocs (it is not shown as you paste it): ").strip()
        if token:
            return token
    raise SystemExit("error: no token. Set GH_TOKEN, or run the script in a terminal to be asked for one (developer/github-settings.md).")


def main(argv: Optional[List[str]] = None, gh: Optional[GitHub] = None, out: Any = None, ask: Callable[[str], str] = input) -> int:
    out = out or sys.stdout
    parser = argparse.ArgumentParser(
        prog="github-settings.py",
        description=f"Check (audit) or apply the GitHub settings baseline of the {ORG} organization (developer/github-settings.md).",
    )
    parser.add_argument("command", choices=("audit", "apply"), help="audit only reads; apply asks before changing anything")
    parser.add_argument("--repo", action="append", metavar="NAME", help="check only this repository (repeatable)")
    parser.add_argument("--yes", action="store_true", help="apply without asking (only after reading the audit)")
    args = parser.parse_args(argv)
    repositories = REPOSITORIES
    if args.repo:
        unknown = [name for name in args.repo if name not in REPOSITORIES]
        if unknown:
            parser.error(f"not in the baseline: {', '.join(unknown)} (add it to REPOSITORIES first)")
        repositories = {name: REPOSITORIES[name] for name in args.repo}
    if gh is None:
        token = read_token()
        kind = token_kind(token)
        if kind != "fine-grained personal access token":
            print(f"warning: this is a {kind}. developer/github-settings.md recommends a fine-grained token for {ORG} only, expiring in 7 days.", file=out)
        gh = GitHub(token)
    try:
        auditor = Auditor(gh, repositories)
        auditor.run()
        status = print_report(auditor, out)
        if args.command == "audit":
            if auditor.changes:
                print("Run `apply` to make the planned changes.", file=out)
            return status
        failed = apply_changes(auditor, args.yes, out, ask)
        if failed is None:
            return status
        print("\nChecking again after the changes:", file=out)
        after = Auditor(gh, repositories)
        after.run()
        status = print_report(after, out)
        return 2 if failed else status
    except ApiError as error:
        print(f"\nerror: {error}", file=out)
        if error.status == 401:
            print("GitHub rejected the token: it may have expired or been mistyped.", file=out)
        return 2
    except urllib.error.URLError as error:
        print(f"\nerror: could not reach {API}: {error.reason}", file=out)
        if isinstance(error.reason, ssl.SSLCertVerificationError):
            print("Python cannot verify GitHub's certificate. With Python from python.org on macOS, run 'Install Certificates.command' from its Applications folder once.", file=out)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted; changes already made stay made. Run audit to see where things stand.", file=sys.stderr)
        sys.exit(130)
