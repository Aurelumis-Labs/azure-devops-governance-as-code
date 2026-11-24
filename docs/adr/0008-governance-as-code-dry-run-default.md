# ADR-0008: Define Azure DevOps branch policies as code, dry-run by default

- **Status:** Proposed
- **Date:** 2026-11-23
- **Decision owner:** Avinash Padaki
- **Jira:** KAN-83
- **Repo / PR:** azure-devops-governance-as-code (PR pending)

## Context

Branch policies configured by hand in the portal drift between repositories, leave no review trail and cannot be reproduced. A tool that changes governance settings must also be safe to run.

## Decision

1. Describe branch policies (reviewers, comment resolution, work item link, merge strategy, build validation) in a YAML file reviewed through pull requests.
2. A small Python tool validates the file and builds the matching `az repos policy` commands. It prints them and runs nothing unless `--apply` is passed.
3. The tool creates policies only. It never edits or deletes existing policies.
4. Environments, approval checks, service connections and agent pools are described in the governance model document and configured outside this tool.

## Alternatives considered

- Manual portal configuration: no review trail, no reproducibility.
- Terraform with the Azure DevOps provider: tracks state and drift, but is heavier to run for this scope.
- REST API scripts: more control, but more code to maintain than the CLI.
- A full reconcile (create, update, delete): closer to desired-state, deferred because deleting policies is risky.

## Consequences

**Benefits:** Governance changes are reviewed like code; a dry run shows exact commands before anything changes; bad input is rejected early.

**Costs and risks:** Re-running can create duplicate policies because the tool is create-only. There is no drift detection. CLI flag names depend on the Azure DevOps extension version.

## Non-goals

Updating or deleting policies, drift detection, environments and approvals as code.

## Validation criteria

`pytest` passes. A dry run prints the expected commands. Apply mode run once against a scratch Azure DevOps project creates each policy exactly once, confirmed with `az repos policy list`.
