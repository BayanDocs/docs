#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BayanDocs contributors
# SPDX-License-Identifier: MIT-0
#
# Tests for scripts/github-settings.py. They run the script against FakeGitHub, an in-memory stand-in for the parts of GitHub's REST API that the script uses, so they need no network and no token. The fake mirrors GitHub's documented behavior where it matters to the script (status codes, pagination, which writes depend on which), but it is not GitHub: the first `audit` against the real organization is the end-to-end check (developer/github-settings.md).
#
# scripts/verify.sh runs them; to run them alone: python3 -m unittest discover -s scripts/tests -v

from __future__ import annotations

import ast
import copy
import importlib.util
import io
import json
import re
import sys
import unittest
import urllib.parse
from unittest import mock
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT = Path(__file__).resolve().parent.parent / "github-settings.py"
_spec = importlib.util.spec_from_file_location("github_settings", SCRIPT)
assert _spec is not None and _spec.loader is not None
gs = importlib.util.module_from_spec(_spec)
sys.modules["github_settings"] = gs  # dataclasses look their module up while the file loads
_spec.loader.exec_module(gs)

TOKEN = "github_pat_11TEST0000000000000000_secretsecretsecretsecretsecretsecretsecretsecretsecretsecr"
EXPIRY = "2026-10-12 10:00:00 UTC"
ORG = "BayanDocs"
PAGE_SIZE = 2  # small pages, so that every list endpoint is read across several pages


def fresh_repository(name: str) -> Dict[str, Any]:
    """A public repository as GitHub creates it, plus the fake's own state (keys starting with "_")."""
    return {
        "name": name,
        "full_name": f"{ORG}/{name}",
        "visibility": "public",
        "archived": False,
        "default_branch": "main",
        "allow_squash_merge": True,
        "allow_merge_commit": True,
        "allow_rebase_merge": True,
        "squash_merge_commit_title": "COMMIT_OR_PR_TITLE",
        "squash_merge_commit_message": "COMMIT_MESSAGES",
        "allow_auto_merge": False,
        "allow_update_branch": False,
        "delete_branch_on_merge": False,
        "has_wiki": True,
        "web_commit_signoff_required": False,
        "security_and_analysis": {
            "secret_scanning": {"status": "enabled"},
            "secret_scanning_push_protection": {"status": "disabled"},
            "dependabot_security_updates": {"status": "disabled"},
        },
        "_alerts": False,
        "_security_updates": False,
        "_reporting": False,
        "_immutable": False,
        "_rulesets": {},
        "_collaborators": [{"login": "owner", "role_name": "admin", "permissions": {"admin": True, "push": True, "pull": True}}],
        "_keys": [],
        "_attached": None,
    }


class FakeGitHub:
    """An in-memory GitHub organization that answers the script's requests like the REST API does."""

    def __init__(self) -> None:
        self.requests: List[Tuple[str, str, Dict[str, str], Any]] = []
        self.unknown: List[str] = []
        self.fail: Dict[Tuple[str, str], Tuple[int, str]] = {}
        self.rate_limit_once: set = set()
        self.clock = 1_800_000_000.0
        self.next_id = 100
        self.login = "owner"
        self.role = "admin"
        self.actions_app_id = 15368
        self.configuration_requests: List[Dict[str, Any]] = []
        self.more_members: Dict[str, str] = {}
        self.without_2fa: set = set()
        self.org: Dict[str, Any] = {
            "login": ORG,
            "default_repository_permission": "read",
            "members_can_create_repositories": True,
            "members_can_create_public_repositories": True,
            "members_can_create_private_repositories": True,
            "members_can_fork_private_repositories": False,
            "members_can_create_pages": True,
            "members_can_create_public_pages": True,
            "members_can_create_private_pages": True,
            "deploy_keys_enabled_for_repositories": True,
            "two_factor_requirement_enabled": False,
        }
        self.private_forks = {"run_workflows_from_fork_pull_requests": False, "send_write_tokens_to_workflows": False, "send_secrets_and_variables": False, "require_approval_for_fork_pr_workflows": True}
        self.immutable = {"enforced_repositories": "none"}
        self.actions = {"enabled_repositories": "all", "allowed_actions": "all", "sha_pinning_required": False}
        self.selected = {"github_owned_allowed": True, "verified_allowed": True, "patterns_allowed": []}
        self.workflow = {"default_workflow_permissions": "write", "can_approve_pull_request_reviews": True}
        self.fork_approval = {"approval_policy": "first_time_contributors"}
        self.configurations: List[Dict[str, Any]] = []
        self.defaults: List[Dict[str, Any]] = []
        self.teams: Dict[str, Dict[str, Any]] = {}
        self.installations = [{"app_slug": "claude", "repository_selection": "selected", "permissions": {"contents": "write", "metadata": "read", "pull_requests": "write"}}]
        self.repos: Dict[str, Dict[str, Any]] = {name: fresh_repository(name) for name in gs.REPOSITORIES}
        r = re.compile
        repo = r"/repos/BayanDocs/(?P<repo>[^/]+)"
        self.routes = [
            ("GET", r(r"/user"), lambda m, q, b: (200, {"login": self.login})),
            ("GET", r(r"/apps/github-actions"), lambda m, q, b: (200, {"id": self.actions_app_id, "slug": "github-actions", "name": "GitHub Actions"})),
            ("GET", r(r"/orgs/BayanDocs/memberships/(?P<login>[^/]+)"), self.get_membership),
            ("GET", r(r"/orgs/BayanDocs"), lambda m, q, b: (200, self.org)),
            ("PATCH", r(r"/orgs/BayanDocs"), self.patch_org),
            ("GET", r(r"/orgs/BayanDocs/actions/permissions"), lambda m, q, b: (200, self.actions)),
            ("PUT", r(r"/orgs/BayanDocs/actions/permissions"), self.put_actions),
            ("GET", r(r"/orgs/BayanDocs/actions/permissions/selected-actions"), self.get_selected),
            ("PUT", r(r"/orgs/BayanDocs/actions/permissions/selected-actions"), self.put_selected),
            ("GET", r(r"/orgs/BayanDocs/actions/permissions/workflow"), lambda m, q, b: (200, self.workflow)),
            ("PUT", r(r"/orgs/BayanDocs/actions/permissions/workflow"), lambda m, q, b: self.replace(self.workflow, b)),
            ("GET", r(r"/orgs/BayanDocs/actions/permissions/fork-pr-contributor-approval"), lambda m, q, b: (200, self.fork_approval)),
            ("PUT", r(r"/orgs/BayanDocs/actions/permissions/fork-pr-contributor-approval"), lambda m, q, b: self.replace(self.fork_approval, b)),
            ("GET", r(r"/orgs/BayanDocs/actions/permissions/fork-pr-workflows-private-repos"), lambda m, q, b: (200, self.private_forks)),
            ("PUT", r(r"/orgs/BayanDocs/actions/permissions/fork-pr-workflows-private-repos"), self.put_private_forks),
            ("GET", r(r"/orgs/BayanDocs/settings/immutable-releases"), lambda m, q, b: (200, dict(self.immutable, selected_repositories_url=f"{gs.API}/orgs/BayanDocs/settings/immutable-releases/repositories"))),
            ("PUT", r(r"/orgs/BayanDocs/settings/immutable-releases"), self.put_immutable),
            ("GET", r(r"/orgs/BayanDocs/code-security/configurations"), lambda m, q, b: (200, self.configurations)),
            ("POST", r(r"/orgs/BayanDocs/code-security/configurations"), self.create_configuration),
            ("GET", r(r"/orgs/BayanDocs/code-security/configurations/defaults"), lambda m, q, b: (200, self.defaults)),
            ("PATCH", r(r"/orgs/BayanDocs/code-security/configurations/(?P<id>\d+)"), self.update_configuration),
            ("PUT", r(r"/orgs/BayanDocs/code-security/configurations/(?P<id>\d+)/defaults"), self.set_default),
            ("GET", r(r"/orgs/BayanDocs/teams"), lambda m, q, b: (200, [self.team_summary(t) for t in self.teams.values()])),
            ("POST", r(r"/orgs/BayanDocs/teams"), self.create_team),
            ("PATCH", r(r"/orgs/BayanDocs/teams/(?P<slug>[^/]+)"), self.update_team),
            ("GET", r(r"/orgs/BayanDocs/teams/(?P<slug>[^/]+)/repos"), self.team_repos),
            ("PUT", r(r"/orgs/BayanDocs/teams/(?P<slug>[^/]+)/repos/BayanDocs/(?P<repo>[^/]+)"), self.set_team_repo),
            ("GET", r(r"/orgs/BayanDocs/teams/(?P<slug>[^/]+)/members"), self.team_members),
            ("GET", r(r"/orgs/BayanDocs/members"), self.members),
            ("GET", r(r"/orgs/BayanDocs/outside_collaborators"), lambda m, q, b: (200, [])),
            ("GET", r(r"/orgs/BayanDocs/installations"), lambda m, q, b: (200, {"total_count": len(self.installations), "installations": self.installations})),
            ("GET", r(r"/orgs/BayanDocs/repos"), lambda m, q, b: (200, [self.public(x) for x in self.repos.values()])),
            ("GET", r(repo), lambda m, q, b: self.with_repo(m, lambda x: (200, self.public(x)))),
            ("PATCH", r(repo), self.patch_repo),
            ("GET", r(repo + "/vulnerability-alerts"), lambda m, q, b: self.with_repo(m, lambda x: (204 if x["_alerts"] else 404, None))),
            ("PUT", r(repo + "/vulnerability-alerts"), lambda m, q, b: self.switch(m, "_alerts", True)),
            ("DELETE", r(repo + "/vulnerability-alerts"), lambda m, q, b: self.switch(m, "_alerts", False)),
            ("GET", r(repo + "/automated-security-fixes"), lambda m, q, b: self.with_repo(m, lambda x: (200, {"enabled": x["_security_updates"], "paused": False}) if x["_alerts"] else (404, {"message": "Not Found"}))),
            ("PUT", r(repo + "/automated-security-fixes"), lambda m, q, b: self.switch(m, "_security_updates", True)),
            ("DELETE", r(repo + "/automated-security-fixes"), lambda m, q, b: self.switch(m, "_security_updates", False)),
            ("GET", r(repo + "/private-vulnerability-reporting"), lambda m, q, b: self.with_repo(m, lambda x: (200, {"enabled": x["_reporting"]}))),
            ("PUT", r(repo + "/private-vulnerability-reporting"), lambda m, q, b: self.switch(m, "_reporting", True)),
            ("DELETE", r(repo + "/private-vulnerability-reporting"), lambda m, q, b: self.switch(m, "_reporting", False)),
            ("GET", r(repo + "/immutable-releases"), lambda m, q, b: self.with_repo(m, self.get_repo_immutable)),
            ("PUT", r(repo + "/immutable-releases"), lambda m, q, b: self.conflict_if_enforced() or self.switch(m, "_immutable", True)),
            ("DELETE", r(repo + "/immutable-releases"), lambda m, q, b: self.conflict_if_enforced() or self.switch(m, "_immutable", False)),
            ("GET", r(repo + "/rulesets"), self.list_rulesets),
            ("POST", r(repo + "/rulesets"), self.create_ruleset),
            ("GET", r(repo + r"/rulesets/(?P<id>\d+)"), self.get_ruleset),
            ("PUT", r(repo + r"/rulesets/(?P<id>\d+)"), self.replace_ruleset),
            ("GET", r(repo + "/code-security-configuration"), lambda m, q, b: self.with_repo(m, lambda x: (200, x["_attached"]) if x["_attached"] else (204, None))),
            ("GET", r(repo + "/collaborators"), lambda m, q, b: self.with_repo(m, lambda x: (200, x["_collaborators"]))),
            ("GET", r(repo + "/keys"), lambda m, q, b: self.with_repo(m, lambda x: (200, x["_keys"]))),
        ]

    # The transport -----------------------------------------------------------

    def __call__(self, method: str, url: str, headers: Dict[str, str], body: Optional[bytes]) -> Tuple[int, Dict[str, str], bytes]:
        data = json.loads(body.decode("utf-8")) if body else None
        self.requests.append((method, url, dict(headers), data))
        parsed = urllib.parse.urlsplit(url)
        if f"{parsed.scheme}://{parsed.netloc}" != gs.API or headers.get("Authorization") != f"Bearer {TOKEN}":
            return self.respond(401, {"message": "Bad credentials"})
        path, query = parsed.path, dict(urllib.parse.parse_qsl(parsed.query))
        if (method, path) in self.fail:
            status, message = self.fail[(method, path)]
            return self.respond(status, {"message": message})
        if (method, path) in self.rate_limit_once:
            self.rate_limit_once.discard((method, path))
            return self.respond(403, {"message": "API rate limit exceeded"}, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(self.clock) + 5)})
        for route_method, pattern, handler in self.routes:
            match = pattern.fullmatch(path)
            if route_method == method and match:
                status, result = handler(match, query, data)
                return self.respond(status, result, page_of=(path, query) if method == "GET" else None)
        self.unknown.append(f"{method} {path}")
        return self.respond(404, {"message": "Not Found"})

    def respond(self, status: int, data: Any, extra: Optional[Dict[str, str]] = None, page_of: Optional[Tuple[str, Dict[str, str]]] = None) -> Tuple[int, Dict[str, str], bytes]:
        headers = {"content-type": "application/json", "github-authentication-token-expiration": EXPIRY}
        headers.update(extra or {})
        if page_of is not None and status == 200:
            data, link = self.paginate(data, *page_of)
            if link:
                headers["link"] = link
        return status, headers, (json.dumps(data).encode("utf-8") if data is not None else b"")

    def paginate(self, data: Any, path: str, query: Dict[str, str]) -> Tuple[Any, Optional[str]]:
        items, key = (data, None) if isinstance(data, list) else (data.get("installations"), "installations") if isinstance(data, dict) and "total_count" in data else (None, None)
        if items is None or "per_page" not in query:
            return data, None
        page = int(query.get("page", "1"))
        chunk = items[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]
        link = None
        if page * PAGE_SIZE < len(items):
            link = f'<{gs.API}{path}?{urllib.parse.urlencode(dict(query, page=str(page + 1)))}>; rel="next"'
        return (chunk if key is None else dict(data, installations=chunk)), link

    # Helpers -----------------------------------------------------------------

    def writes(self) -> List[Tuple[str, str]]:
        return [(method, urllib.parse.urlsplit(url).path) for method, url, _, _ in self.requests if method != "GET"]

    @staticmethod
    def replace(target: Dict[str, Any], body: Dict[str, Any]) -> Tuple[int, Any]:
        target.clear()
        target.update(body)
        return 204, None

    @staticmethod
    def public(repo: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in repo.items() if not k.startswith("_")}

    def with_repo(self, match: Any, action: Any) -> Tuple[int, Any]:
        repo = self.repos.get(match["repo"])
        return action(repo) if repo else (404, {"message": "Not Found"})

    def switch(self, match: Any, key: str, value: bool) -> Tuple[int, Any]:
        def act(repo: Dict[str, Any]) -> Tuple[int, Any]:
            repo[key] = value
            return 204, None

        return self.with_repo(match, act)

    def new_id(self) -> int:
        self.next_id += 1
        return self.next_id

    # Organization ------------------------------------------------------------

    def get_membership(self, match: Any, query: Any, body: Any) -> Tuple[int, Any]:
        if match["login"] != self.login:
            return 404, {"message": "Not Found"}
        return 200, {"role": self.role, "state": "active"}

    def patch_org(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        self.org.update(body)
        return 200, self.org

    def put_actions(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        if "enabled_repositories" not in body:
            return 422, {"message": "enabled_repositories is required"}
        return self.replace(self.actions, body)

    def get_selected(self, match: Any, query: Any, body: Any) -> Tuple[int, Any]:
        if self.actions.get("allowed_actions") != "selected":
            return 409, {"message": "allowed_actions is not selected"}
        return 200, self.selected

    def put_selected(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        if self.actions.get("allowed_actions") != "selected":
            return 409, {"message": "allowed_actions is not selected"}
        return self.replace(self.selected, body)

    def put_private_forks(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        if "run_workflows_from_fork_pull_requests" not in body:
            return 422, {"message": "run_workflows_from_fork_pull_requests is required"}
        self.private_forks.update(body)
        return 204, None

    def put_immutable(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        if body.get("enforced_repositories") not in ("all", "none", "selected"):
            return 422, {"message": "enforced_repositories is required"}
        self.immutable = {"enforced_repositories": body["enforced_repositories"]}
        return 204, None

    def get_repo_immutable(self, repo: Dict[str, Any]) -> Tuple[int, Any]:
        # Documented: 200 when immutable releases are on, 404 when they are off.
        enforced = self.immutable["enforced_repositories"] == "all"
        if enforced or repo["_immutable"]:
            return 200, {"enabled": True, "enforced_by_owner": enforced}
        return 404, {"message": "Not Found"}

    def conflict_if_enforced(self) -> Optional[Tuple[int, Any]]:
        if self.immutable["enforced_repositories"] == "all":
            return 409, {"message": "Immutable releases are enforced by the organization"}
        return None

    def create_configuration(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        self.configuration_requests.append(body)
        body = {k: v for k, v in body.items() if k not in ("secret_protection", "code_security")}
        configuration = dict(body, id=self.new_id(), target_type="organization")
        self.configurations.append(configuration)
        return 201, configuration

    def find_configuration(self, identifier: str) -> Optional[Dict[str, Any]]:
        return next((c for c in self.configurations if c["id"] == int(identifier)), None)

    def update_configuration(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        configuration = self.find_configuration(match["id"])
        if configuration is None:
            return 404, {"message": "Not Found"}
        self.configuration_requests.append(body)
        configuration.update({k: v for k, v in body.items() if k not in ("secret_protection", "code_security")})
        return 200, configuration

    def set_default(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        configuration = self.find_configuration(match["id"])
        if configuration is None:
            return 404, {"message": "Not Found"}
        self.defaults = [d for d in self.defaults if d["default_for_new_repos"] != body["default_for_new_repos"]]
        self.defaults.append({"default_for_new_repos": body["default_for_new_repos"], "configuration": configuration})
        return 200, {"default_for_new_repos": body["default_for_new_repos"], "configuration": configuration}

    @staticmethod
    def team_summary(team: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in team.items() if k in ("name", "slug", "description", "privacy")}

    def create_team(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        slug = body["name"].lower().replace(" ", "-")
        if slug in self.teams:
            return 422, {"message": "Name must be unique for this org"}
        # GitHub makes the person who creates a team its first maintainer.
        self.teams[slug] = {"name": body["name"], "slug": slug, "description": body.get("description", ""), "privacy": body.get("privacy", "secret"), "repos": {}, "members": [self.login]}
        return 201, self.team_summary(self.teams[slug])

    def update_team(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        team = self.teams.get(match["slug"])
        if team is None:
            return 404, {"message": "Not Found"}
        team.update(body)
        return 200, self.team_summary(team)

    def team_repos(self, match: Any, query: Any, body: Any) -> Tuple[int, Any]:
        team = self.teams.get(match["slug"])
        if team is None:
            return 404, {"message": "Not Found"}
        return 200, [{"name": repo, "role_name": gs.ROLE_NAMES[permission]} for repo, permission in team["repos"].items()]

    def set_team_repo(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        team = self.teams.get(match["slug"])
        if team is None or match["repo"] not in self.repos:
            return 404, {"message": "Not Found"}
        if body.get("permission") not in gs.ROLE_NAMES:
            return 422, {"message": "invalid permission"}
        team["repos"][match["repo"]] = body["permission"]
        return 204, None

    def team_members(self, match: Any, query: Any, body: Any) -> Tuple[int, Any]:
        team = self.teams.get(match["slug"])
        if team is None:
            return 404, {"message": "Not Found"}
        return 200, [{"login": login} for login in team["members"]]

    def members(self, match: Any, query: Dict[str, str], body: Any) -> Tuple[int, Any]:
        wanted = query.get("role", "all")
        everyone = {self.login: self.role, **self.more_members}
        if query.get("filter") == "2fa_disabled":
            return 200, [{"login": login} for login in sorted(self.without_2fa)]
        if query.get("filter", "all") != "all":
            return 200, []
        return 200, [{"login": login} for login, role in everyone.items() if wanted in ("all", role)]

    # Repositories ------------------------------------------------------------

    def patch_repo(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        repo = self.repos.get(match["repo"])
        if repo is None:
            return 404, {"message": "Not Found"}
        if ("squash_merge_commit_title" in body) != ("squash_merge_commit_message" in body):
            return 422, {"message": "squash_merge_commit_title and squash_merge_commit_message must be set together"}
        for key, value in body.items():
            if key == "security_and_analysis":
                for feature, setting in value.items():
                    repo["security_and_analysis"][feature] = dict(setting)
            else:
                repo[key] = value
        return 200, self.public(repo)

    def stored_ruleset(self, repo: Dict[str, Any], body: Dict[str, Any], identifier: int) -> Dict[str, Any]:
        ruleset = copy.deepcopy(body)
        ruleset.update(id=identifier, source_type="Repository", source=f"{ORG}/{repo['name']}", node_id=f"RRS_{identifier}", created_at="2026-10-05T10:00:00Z", updated_at="2026-10-05T10:00:00Z", current_user_can_bypass="never")
        for actor in ruleset["bypass_actors"]:
            actor.setdefault("bypass_mode", "always")
        for rule in ruleset["rules"]:
            # GitHub returns parameters the request left out with their default values.
            if rule["type"] == "pull_request":
                rule["parameters"].setdefault("required_reviewers", [])
            if rule["type"] == "required_status_checks":
                rule["parameters"]["required_status_checks"].reverse()  # any order
            # GitHub accepts the update rule's update_allows_fetch_and_merge, but leaves it out of its answer when it is false (seen on the release-tag rulesets, 2026-10-06).
            if rule["type"] == "update" and rule.get("parameters", {}).get("update_allows_fetch_and_merge") is False:
                del rule["parameters"]
        return ruleset

    def list_rulesets(self, match: Any, query: Any, body: Any) -> Tuple[int, Any]:
        return self.with_repo(match, lambda repo: (200, [{k: r[k] for k in ("id", "name", "target", "enforcement", "source_type", "source")} for r in repo["_rulesets"].values()]))

    def create_ruleset(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        def act(repo: Dict[str, Any]) -> Tuple[int, Any]:
            if any(r["name"] == body["name"] for r in repo["_rulesets"].values()):
                return 422, {"message": "Name must be unique"}
            identifier = self.new_id()
            repo["_rulesets"][identifier] = self.stored_ruleset(repo, body, identifier)
            return 201, repo["_rulesets"][identifier]

        return self.with_repo(match, act)

    def get_ruleset(self, match: Any, query: Any, body: Any) -> Tuple[int, Any]:
        return self.with_repo(match, lambda repo: (200, repo["_rulesets"][int(match["id"])]) if int(match["id"]) in repo["_rulesets"] else (404, {"message": "Not Found"}))

    def replace_ruleset(self, match: Any, query: Any, body: Dict[str, Any]) -> Tuple[int, Any]:
        def act(repo: Dict[str, Any]) -> Tuple[int, Any]:
            identifier = int(match["id"])
            if identifier not in repo["_rulesets"]:
                return 404, {"message": "Not Found"}
            repo["_rulesets"][identifier] = self.stored_ruleset(repo, body, identifier)
            return 200, repo["_rulesets"][identifier]

        return self.with_repo(match, act)


class Run:
    """One run of the script's command line against a fake GitHub."""

    def __init__(self, fake: FakeGitHub, *argv: str, answer: str = "apply") -> None:
        self.sleeps: List[float] = []

        def sleep(seconds: float) -> None:
            self.sleeps.append(seconds)
            fake.clock += seconds

        gh = gs.GitHub(TOKEN, transport=fake, sleep=sleep, clock=lambda: fake.clock)
        out = io.StringIO()
        self.questions: List[str] = []

        def ask(question: str) -> str:
            self.questions.append(question)
            return answer

        self.status = gs.main(list(argv), gh=gh, out=out, ask=ask)
        self.output = out.getvalue()


def reach_baseline(fake: FakeGitHub) -> None:
    """Applies the baseline and does by hand what the API cannot."""
    Run(fake, "apply", "--yes")
    fake.org["two_factor_requirement_enabled"] = True


class GitHubSettingsTest(unittest.TestCase):
    def test_script_runs_on_python_3_9(self) -> None:
        # macOS ships Python 3.9 as /usr/bin/python3, so the script must not use newer syntax.
        ast.parse(SCRIPT.read_text(encoding="utf-8"), feature_version=(3, 9))

    def test_audit_of_a_new_organization_reports_differences_and_changes_nothing(self) -> None:
        fake = FakeGitHub()
        run = Run(fake, "audit")
        self.assertEqual(run.status, 1, run.output)
        self.assertIn('DRIFT  Base permission of members: "read", baseline "none"', run.output)
        self.assertIn('DRIFT  Ruleset "Protect main": missing', run.output)
        self.assertIn("DRIFT  Team Maintainers: missing", run.output)
        self.assertIn("DRIFT  Dependabot alerts: false, baseline true", run.output)
        self.assertNotIn("ERROR  ", run.output)
        self.assertEqual(fake.writes(), [])
        self.assertEqual(fake.unknown, [])

    def test_apply_reaches_the_baseline_and_a_second_apply_changes_nothing(self) -> None:
        fake = FakeGitHub()
        first = Run(fake, "apply", "--yes")
        self.assertNotIn("FAILED", first.output)
        self.assertEqual(first.questions, [])
        # Two-factor authentication can only be required in the web interface, so it still differs.
        self.assertEqual(first.status, 1, first.output)
        self.assertIn("Require two-factor authentication", first.output)
        fake.org["two_factor_requirement_enabled"] = True
        audit = Run(fake, "audit")
        self.assertEqual(audit.status, 0, audit.output)
        self.assertNotIn("DRIFT", audit.output)
        writes = len(fake.writes())
        second = Run(fake, "apply", "--yes")
        self.assertEqual(second.status, 0, second.output)
        self.assertIn("Nothing to change", second.output)
        self.assertEqual(len(fake.writes()), writes)
        self.assertEqual(fake.unknown, [])

    def test_apply_sets_what_the_baseline_says(self) -> None:
        fake = FakeGitHub()
        reach_baseline(fake)
        self.assertEqual(fake.org["default_repository_permission"], "none")
        self.assertEqual(fake.actions, {"enabled_repositories": "all", "allowed_actions": "selected", "sha_pinning_required": True})
        self.assertEqual(fake.selected, {"github_owned_allowed": True, "verified_allowed": False, "patterns_allowed": []})
        self.assertEqual(fake.workflow, {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False})
        self.assertEqual(fake.fork_approval, {"approval_policy": "all_external_contributors"})
        self.assertEqual([d["default_for_new_repos"] for d in fake.defaults], ["public"])
        self.assertEqual(fake.defaults[0]["configuration"]["dependabot_security_updates"], "disabled")
        self.assertEqual(fake.teams["maintainers"]["repos"], {name: "maintain" for name in gs.REPOSITORIES})
        self.assertEqual(fake.teams["triage"]["repos"], {name: "triage" for name in gs.REPOSITORIES})
        self.assertFalse(fake.org["members_can_create_public_pages"] or fake.org["members_can_create_private_pages"])
        self.assertEqual(fake.immutable, {"enforced_repositories": "all"})
        for name, repo in fake.repos.items():
            self.assertTrue(repo["_alerts"] and repo["_reporting"], name)
            self.assertFalse(repo["_security_updates"], name)
            self.assertEqual(repo["security_and_analysis"]["secret_scanning_push_protection"], {"status": "enabled"})
            self.assertEqual((repo["allow_squash_merge"], repo["allow_merge_commit"], repo["allow_rebase_merge"]), (True, False, False))
            self.assertEqual(sorted(r["name"] for r in repo["_rulesets"].values()), ["Protect main", "Protect release tags"])
        main = next(r for r in fake.repos["bayan-core"]["_rulesets"].values() if r["name"] == "Protect main")
        checks = next(rule for rule in main["rules"] if rule["type"] == "required_status_checks")["parameters"]
        self.assertEqual(sorted(c["context"] for c in checks["required_status_checks"]), sorted(gs.REPOSITORIES["bayan-core"]))
        self.assertTrue(all(c["integration_id"] == gs.GITHUB_ACTIONS_APP_ID for c in checks["required_status_checks"]))

    def test_every_repository_requires_the_dco_and_reuse_checks(self) -> None:
        fake = FakeGitHub()
        reach_baseline(fake)
        for name, repo in fake.repos.items():
            main = next(r for r in repo["_rulesets"].values() if r["name"] == "Protect main")
            checks = next(rule for rule in main["rules"] if rule["type"] == "required_status_checks")["parameters"]
            contexts = [c["context"] for c in checks["required_status_checks"]]
            self.assertIn("DCO", contexts, name)
            self.assertIn("REUSE lint", contexts, name)

    def test_web_commits_and_merges_are_signed_off(self) -> None:
        fake = FakeGitHub()
        audit = Run(fake, "audit")
        self.assertIn("DRIFT  Commits made in the web interface, merges included, are signed off: false, baseline true", audit.output)
        reach_baseline(fake)
        self.assertTrue(all(repo["web_commit_signoff_required"] for repo in fake.repos.values()))
        self.assertIn(("PATCH", "/repos/BayanDocs/docs"), fake.writes())

    def test_a_repository_without_ci_gets_no_required_checks_rule(self) -> None:
        with mock.patch.dict(gs.REPOSITORIES, {"no-ci": []}):
            fake = FakeGitHub()
            reach_baseline(fake)
            main = next(r for r in fake.repos["no-ci"]["_rulesets"].values() if r["name"] == "Protect main")
            self.assertNotIn("required_status_checks", [rule["type"] for rule in main["rules"]])
            self.assertEqual(Run(fake, "audit").status, 0)

    def test_writes_that_depend_on_each_other_come_in_order(self) -> None:
        fake = FakeGitHub()
        Run(fake, "apply", "--yes")
        writes = fake.writes()
        self.assertLess(writes.index(("PUT", "/orgs/BayanDocs/actions/permissions")), writes.index(("PUT", "/orgs/BayanDocs/actions/permissions/selected-actions")))
        self.assertLess(writes.index(("POST", "/orgs/BayanDocs/teams")), writes.index(("PUT", "/orgs/BayanDocs/teams/maintainers/repos/BayanDocs/docs")))

    def test_writes_are_at_least_a_second_apart(self) -> None:
        fake = FakeGitHub()
        run = Run(fake, "apply", "--yes")
        times = [t for t in run.sleeps]
        self.assertGreaterEqual(len(times), len(fake.writes()) - 1)
        self.assertTrue(all(t <= gs.WRITE_INTERVAL for t in times))

    def test_the_token_is_only_sent_to_the_api_and_never_printed(self) -> None:
        fake = FakeGitHub()
        run = Run(fake, "apply", "--yes")
        self.assertNotIn(TOKEN, run.output)
        self.assertNotIn(TOKEN[12:], run.output)
        self.assertNotIn(TOKEN, repr(gs.GitHub(TOKEN)))
        for method, url, headers, _ in fake.requests:
            self.assertTrue(url.startswith(gs.API + "/"), url)
            self.assertEqual(headers["Authorization"], f"Bearer {TOKEN}")
            self.assertEqual(headers["X-GitHub-Api-Version"], gs.API_VERSION)
            self.assertIn("User-Agent", headers)

    def test_declining_the_question_changes_nothing(self) -> None:
        fake = FakeGitHub()
        run = Run(fake, "apply", answer="no")
        self.assertEqual(len(run.questions), 1)
        self.assertIn("Nothing was changed.", run.output)
        self.assertEqual(fake.writes(), [])

    def test_rulesets_match_despite_defaults_and_order_github_adds(self) -> None:
        fake = FakeGitHub()
        reach_baseline(fake)
        run = Run(fake, "audit")
        self.assertIn('ok     Ruleset "Protect main": matches the baseline', run.output)
        self.assertIn('ok     Ruleset "Protect release tags": matches the baseline', run.output)
        self.assertEqual(run.status, 0, run.output)

    def test_a_tag_rule_that_allows_fetch_and_merge_is_still_reported(self) -> None:
        # GitHub's answer leaves out update_allows_fetch_and_merge when it is false, so only its absence counts as false.
        fake = FakeGitHub()
        reach_baseline(fake)
        tags = next(r for r in fake.repos["docs"]["_rulesets"].values() if r["name"] == "Protect release tags")
        update = next(rule for rule in tags["rules"] if rule["type"] == "update")
        update["parameters"] = {"update_allows_fetch_and_merge": True}
        audit = Run(fake, "audit")
        self.assertEqual(audit.status, 1, audit.output)
        self.assertIn('DRIFT  Ruleset "Protect release tags": rule update: update_allows_fetch_and_merge is true, baseline false', audit.output)
        before = len(fake.writes())
        Run(fake, "apply", "--yes")
        self.assertEqual(fake.writes()[before:], [("PUT", f"/repos/BayanDocs/docs/rulesets/{tags['id']}")])
        self.assertEqual(Run(fake, "audit").status, 0)

    def test_an_edited_ruleset_is_repaired_in_place(self) -> None:
        fake = FakeGitHub()
        reach_baseline(fake)
        main = next(r for r in fake.repos["docs"]["_rulesets"].values() if r["name"] == "Protect main")
        main["rules"] = [rule for rule in main["rules"] if rule["type"] != "required_linear_history"]
        main["bypass_actors"] = [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]
        audit = Run(fake, "audit")
        self.assertEqual(audit.status, 1)
        self.assertIn('DRIFT  Ruleset "Protect main": lacks the rule required_linear_history', audit.output)
        self.assertIn('DRIFT  Ruleset "Protect main": bypass list is', audit.output)
        before = len(fake.writes())
        Run(fake, "apply", "--yes")
        self.assertEqual(fake.writes()[before:], [("PUT", f"/repos/BayanDocs/docs/rulesets/{main['id']}")])
        self.assertEqual(Run(fake, "audit").status, 0)

    def test_other_repositories_are_reported_but_never_changed(self) -> None:
        fake = FakeGitHub()
        fake.repos["playground"] = fresh_repository("playground")
        fake.repos["old"] = dict(fresh_repository("old"), archived=True)
        run = Run(fake, "apply", "--yes")
        self.assertIn("DRIFT  Repository playground is not in the baseline", run.output)
        self.assertIn("info   Repository old is archived; not checked", run.output)
        touched = [path for _, path in fake.writes() if "/playground" in path or "/old" in path]
        self.assertEqual(touched, [])

    def test_a_failed_change_is_reported_and_the_others_still_run(self) -> None:
        fake = FakeGitHub()
        fake.fail[("PUT", "/repos/BayanDocs/docs/private-vulnerability-reporting")] = (403, "Resource not accessible by personal access token")
        run = Run(fake, "apply", "--yes")
        self.assertEqual(run.status, 2)
        self.assertIn("FAILED: repository docs: turn on private vulnerability reporting", run.output)
        self.assertTrue(fake.repos["bayan-core"]["_reporting"])

    def test_immutable_releases_are_enforced_once_for_the_whole_organization(self) -> None:
        fake = FakeGitHub()
        run = Run(fake, "apply", "--yes")
        self.assertIn("DRIFT  Immutable releases: false, baseline true; set by the organization's immutable releases setting", run.output)
        self.assertNotIn(("PUT", "/repos/BayanDocs/docs/immutable-releases"), fake.writes())
        self.assertNotIn("FAILED", run.output)
        self.assertIn("ok     Immutable releases: true", run.output.split("Checking again after the changes:", 1)[1])

    def test_immutable_releases_fall_back_to_each_repository(self) -> None:
        fake = FakeGitHub()
        fake.fail[("GET", "/orgs/BayanDocs/settings/immutable-releases")] = (404, "Not Found")
        run = Run(fake, "apply", "--yes")
        self.assertIn(("PUT", "/repos/BayanDocs/docs/immutable-releases"), fake.writes())
        self.assertTrue(all(repo["_immutable"] for repo in fake.repos.values()))
        self.assertEqual(run.status, 2)  # the organization setting could not be checked

    def test_merge_settings_hidden_from_the_token_are_explained(self) -> None:
        fake = FakeGitHub()
        for key in ("allow_squash_merge", "allow_merge_commit", "allow_rebase_merge", "squash_merge_commit_title", "squash_merge_commit_message", "allow_auto_merge", "allow_update_branch", "delete_branch_on_merge"):
            del fake.repos["docs"][key]
        run = Run(fake, "audit")
        self.assertIn("ERROR  Squash merging allowed: GitHub's answer has no allow_squash_merge (GitHub shows merge settings only to tokens with the Contents permission, read and write)", run.output)

    def test_private_fork_workflows_are_switched_off(self) -> None:
        fake = FakeGitHub()
        fake.private_forks["run_workflows_from_fork_pull_requests"] = True
        audit = Run(fake, "audit")
        self.assertIn("DRIFT  Workflows run on pull requests from forks of private repositories: true, baseline false", audit.output)
        Run(fake, "apply", "--yes")
        self.assertFalse(fake.private_forks["run_workflows_from_fork_pull_requests"])

    def test_a_field_missing_from_the_answer_is_an_error_not_a_change(self) -> None:
        fake = FakeGitHub()
        del fake.org["deploy_keys_enabled_for_repositories"]
        run = Run(fake, "apply", "--yes")
        self.assertIn("ERROR  Deploy keys allowed: GitHub's answer has no deploy_keys_enabled_for_repositories", run.output)
        patches = [data for method, url, _, data in fake.requests if method == "PATCH" and url.endswith("/orgs/BayanDocs")]
        self.assertTrue(patches)
        self.assertNotIn("deploy_keys_enabled_for_repositories", patches[0])
        self.assertEqual(run.status, 2)

    def test_a_refusal_in_one_check_does_not_hide_the_others(self) -> None:
        fake = FakeGitHub()
        fake.fail[("GET", "/orgs/BayanDocs/actions/permissions")] = (403, "Resource not accessible by personal access token")
        run = Run(fake, "audit")
        self.assertEqual(run.status, 2)
        self.assertIn("ERROR  GET /orgs/BayanDocs/actions/permissions failed with HTTP 403", run.output)
        self.assertIn('DRIFT  Ruleset "Protect main": missing', run.output)

    def test_one_refused_feature_check_does_not_hide_the_next(self) -> None:
        fake = FakeGitHub()
        fake.fail[("GET", "/repos/BayanDocs/docs/automated-security-fixes")] = (403, "Resource not accessible by personal access token")
        run = Run(fake, "audit")
        docs = run.output.split("Repository docs", 1)[1].split("Repository bayan-core", 1)[0]
        self.assertIn("ERROR  GET /repos/BayanDocs/docs/automated-security-fixes failed with HTTP 403", docs)
        self.assertIn("DRIFT  Private vulnerability reporting: false, baseline true", docs)
        self.assertIn("DRIFT  Immutable releases: false, baseline true", docs)

    def test_an_unexpected_answer_is_an_error_not_a_crash(self) -> None:
        fake = FakeGitHub()
        fake.routes.insert(0, ("GET", re.compile(r"/repos/BayanDocs/docs/private-vulnerability-reporting"), lambda m, q, b: (200, {"surprise": True})))
        run = Run(fake, "audit")
        self.assertEqual(run.status, 2)
        self.assertIn("ERROR  unexpected answer from GitHub (KeyError: 'enabled')", run.output)
        self.assertIn('DRIFT  Ruleset "Protect main": missing', run.output)

    def test_a_closed_input_counts_as_no(self) -> None:
        fake = FakeGitHub()
        gh = gs.GitHub(TOKEN, transport=fake, sleep=lambda s: None, clock=lambda: fake.clock)

        def closed(question: str) -> str:
            raise EOFError

        out = io.StringIO()
        gs.main(["apply"], gh=gh, out=out, ask=closed)
        self.assertIn("Nothing was changed.", out.getvalue())
        self.assertEqual(fake.writes(), [])

    def test_rate_limits_are_waited_out(self) -> None:
        fake = FakeGitHub()
        fake.rate_limit_once.add(("GET", "/orgs/BayanDocs"))
        run = Run(fake, "audit")
        self.assertIn(6.0, run.sleeps)
        self.assertNotIn("ERROR", run.output)

    def test_only_the_named_repository_is_checked(self) -> None:
        fake = FakeGitHub()
        Run(fake, "apply", "--yes", "--repo", "docs")
        repo_writes = {path.split("/")[3] for _, path in fake.writes() if path.startswith("/repos/")}
        self.assertEqual(repo_writes, {"docs"})
        self.assertEqual(fake.teams["maintainers"]["repos"], {"docs": "maintain"})

    def test_a_rejected_token_stops_with_an_explanation(self) -> None:
        fake = FakeGitHub()
        fake.fail[("GET", "/user")] = (401, "Bad credentials")
        run = Run(fake, "audit")
        self.assertEqual(run.status, 2)
        self.assertIn("GitHub rejected the token", run.output)

    def test_someone_who_is_not_an_owner_is_told_so(self) -> None:
        fake = FakeGitHub()
        fake.role = "member"
        run = Run(fake, "audit")
        self.assertIn('ERROR  Signed in as owner, whose role is "member": only owners can change these settings', run.output)

    def test_people_who_would_lose_access_under_two_factor_rules_are_listed(self) -> None:
        fake = FakeGitHub()
        fake.more_members = {"helper": "member"}
        fake.without_2fa = {"helper"}
        run = Run(fake, "audit")
        self.assertIn("info   Members who are not owners: helper", run.output)
        self.assertIn("info   Members and outside collaborators without two-factor authentication: helper", run.output)
        self.assertIn("info   Members and outside collaborators whose only second factor is insecure (such as SMS): none", run.output)

    def test_a_wrong_actions_app_id_blocks_required_checks_but_nothing_else(self) -> None:
        with mock.patch.dict(gs.REPOSITORIES, {"no-ci": []}):
            fake = FakeGitHub()
            fake.actions_app_id = 99
            run = Run(fake, "apply", "--yes")
        self.assertIn("ERROR  App ID of GitHub Actions is 99, but the baseline says 15368", run.output)
        self.assertIn('ERROR  Ruleset "Protect main": not changed, because the app ID of GitHub Actions is not confirmed', run.output)
        created = {path for method, path in fake.writes() if method == "POST" and path.endswith("/rulesets")}
        # A repository without required checks names no app, so its rules are safe to apply; release tag rules never name one.
        self.assertNotIn("Protect main", [r["name"] for r in fake.repos["docs"]["_rulesets"].values()])
        self.assertIn("Protect main", [r["name"] for r in fake.repos["no-ci"]["_rulesets"].values()])
        self.assertIn("/repos/BayanDocs/docs/rulesets", created)
        self.assertEqual(run.status, 2)

    def test_security_updates_read_as_off_when_dependabot_is_off(self) -> None:
        fake = FakeGitHub()
        run = Run(fake, "audit")
        self.assertIn("ok     Dependabot security update pull requests: false", run.output)
        self.assertNotIn("ERROR  ", run.output)

    def test_the_configuration_includes_its_product_and_the_attachment_is_reported(self) -> None:
        fake = FakeGitHub()
        fake.repos["docs"]["_attached"] = {"status": "enforced", "configuration": {"id": 1, "name": "GitHub recommended"}}
        run = Run(fake, "apply", "--yes")
        self.assertEqual(fake.configuration_requests[0]["secret_protection"], "enabled")
        self.assertIn('info   Security configuration attached: "GitHub recommended", status enforced', run.output)
        self.assertIn("info   Security configuration attached: none (settings are made directly)", run.output)

    def test_the_token_expiry_is_shown(self) -> None:
        run = Run(FakeGitHub(), "audit")
        self.assertIn(f"The token expires {EXPIRY}.", run.output)

    def test_page_links_must_stay_on_the_api(self) -> None:
        self.assertEqual(gs._next_page(f'<{gs.API}/orgs/x/repos?page=2>; rel="next", <{gs.API}/orgs/x/repos?page=9>; rel="last"'), "/orgs/x/repos?page=2")
        self.assertIsNone(gs._next_page(f'<{gs.API}/orgs/x/repos?page=1>; rel="prev"'))
        with self.assertRaises(ValueError):
            gs._next_page('<https://example.com/steal?page=2>; rel="next"')

    def test_patch_accepts_every_success_answer(self) -> None:
        # Documented: a security configuration answers 204 when nothing changed, a team 201.
        for status in (200, 201, 204):
            gh = gs.GitHub(TOKEN, transport=lambda method, url, headers, body, status=status: (status, {}, b""), sleep=lambda seconds: None)
            gh.patch("/orgs/BayanDocs/code-security/configurations/1", {"description": "x"})

    def test_redirects_are_refused(self) -> None:
        self.assertIsNone(gs._NoRedirects().redirect_request(None, None, 301, "Moved", {}, "https://example.com/"))

    def test_token_kinds(self) -> None:
        self.assertEqual(gs.token_kind("github_pat_abc"), "fine-grained personal access token")
        self.assertEqual(gs.token_kind("ghp_abc"), "classic personal access token")
        self.assertEqual(gs.token_kind("gho_abc"), "OAuth token (such as the GitHub CLI's)")

    def test_the_main_ruleset_requires_checks_from_github_actions_only(self) -> None:
        with_checks = gs.main_branch_ruleset(["a", "b"])
        rule = next(r for r in with_checks["rules"] if r["type"] == "required_status_checks")
        self.assertEqual(rule["parameters"]["required_status_checks"], [{"context": "a", "integration_id": 15368}, {"context": "b", "integration_id": 15368}])
        self.assertTrue(rule["parameters"]["strict_required_status_checks_policy"])
        self.assertEqual([r["type"] for r in gs.main_branch_ruleset([])["rules"]], ["deletion", "non_fast_forward", "required_linear_history", "pull_request"])


if __name__ == "__main__":
    unittest.main()
