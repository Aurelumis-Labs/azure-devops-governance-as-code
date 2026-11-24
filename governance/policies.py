"""Turn a governance definition into `az repos policy` commands.

Dry-run by default: nothing runs unless the caller passes apply=True.
Policies are authoritative in Azure DevOps; this tool only creates policies and
never edits or deletes existing ones, so re-running it can create duplicates.
Check existing policies first (`az repos policy list`).
"""
from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass

MERGE_STRATEGIES = {
    "squash": dict(squash="true", no_ff="false", rebase="false", rebase_merge="false"),
    "merge": dict(squash="false", no_ff="true", rebase="false", rebase_merge="false"),
    "rebase": dict(squash="false", no_ff="false", rebase="true", rebase_merge="false"),
}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Command:
    description: str
    argv: tuple[str, ...]

    def shell(self) -> str:
        return " ".join(shlex.quote(a) for a in self.argv)


def _base(kind: str, repo_id: str, branch: str, org: str, project: str, blocking: bool = True) -> list[str]:
    return [
        "az", "repos", "policy", kind, "create",
        "--organization", org, "--project", project,
        "--repository-id", repo_id, "--branch", branch,
        "--blocking", str(blocking).lower(), "--enabled", "true",
    ]


def build_commands(config: dict, repo_ids: dict[str, str] | None = None) -> list[Command]:
    """Return the commands for every branch policy in the definition."""
    for key in ("organization", "project", "repositories"):
        if key not in config:
            raise ConfigError(f"missing '{key}'")
    org, project = config["organization"], config["project"]
    repo_ids = repo_ids or {}
    commands: list[Command] = []

    for repo in config["repositories"]:
        name = repo["name"]
        repo_id = repo_ids.get(name, f"<id:{name}>")
        for branch in repo.get("branches", []):
            ref = branch["name"]
            p = branch.get("policies", {})
            label = f"{name}@{ref}"

            if "min_reviewers" in p:
                n = int(p["min_reviewers"])
                if n < 1:
                    raise ConfigError(f"{label}: min_reviewers must be >= 1")
                commands.append(Command(f"{label}: require {n} reviewers", tuple(
                    _base("approver-count", repo_id, ref, org, project) + [
                        "--minimum-approver-count", str(n),
                        "--creator-vote-counts", str(p.get("creator_vote_counts", False)).lower(),
                        "--allow-downvotes", "false",
                        "--reset-on-source-push", str(p.get("reset_votes_on_push", True)).lower(),
                    ])))

            if p.get("require_comment_resolution"):
                commands.append(Command(f"{label}: require comment resolution", tuple(
                    _base("comment-required", repo_id, ref, org, project))))

            if p.get("require_work_item_link"):
                commands.append(Command(f"{label}: require linked work item", tuple(
                    _base("work-item-linking", repo_id, ref, org, project))))

            if "merge_strategy" in p:
                strategy = p["merge_strategy"]
                if strategy not in MERGE_STRATEGIES:
                    raise ConfigError(f"{label}: merge_strategy must be one of {sorted(MERGE_STRATEGIES)}")
                m = MERGE_STRATEGIES[strategy]
                commands.append(Command(f"{label}: allow only {strategy} merges", tuple(
                    _base("merge-strategy", repo_id, ref, org, project) + [
                        "--allow-squash", m["squash"],
                        "--allow-no-fast-forward", m["no_ff"],
                        "--allow-rebase", m["rebase"],
                        "--allow-rebase-merge", m["rebase_merge"],
                    ])))

            for bv in p.get("build_validation", []):
                commands.append(Command(f"{label}: build validation '{bv['display_name']}'", tuple(
                    _base("build", repo_id, ref, org, project) + [
                        "--build-definition-id", str(bv["pipeline_id"]),
                        "--display-name", bv["display_name"],
                        "--queue-on-source-update-only", "true",
                        "--manual-queue-only", "false",
                        "--valid-duration", str(bv.get("valid_duration_minutes", 720)),
                    ])))
    return commands


def resolve_repo_ids(config: dict) -> dict[str, str]:
    """Look up repository ids with the Azure CLI (read-only)."""
    ids = {}
    for repo in config["repositories"]:
        out = subprocess.run(
            ["az", "repos", "show", "--repository", repo["name"],
             "--organization", config["organization"], "--project", config["project"],
             "--query", "id", "-o", "tsv"],
            check=True, capture_output=True, text=True)
        ids[repo["name"]] = out.stdout.strip()
    return ids


def run(config: dict, apply: bool = False) -> list[Command]:
    ids = resolve_repo_ids(config) if apply else None
    commands = build_commands(config, ids)
    for c in commands:
        print(("APPLY  " if apply else "DRY-RUN  ") + c.description)
        if not apply:
            print("    " + c.shell())
        else:
            subprocess.run(c.argv, check=True)
    return commands
