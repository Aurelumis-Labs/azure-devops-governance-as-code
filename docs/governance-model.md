# Governance model

A platform team owns the rules; application teams own the code. The model separates *who can change a rule* from *who can use it*.

| Control | Where it lives | Who changes it |
| --- | --- | --- |
| Branch policies (reviewers, comment resolution, work item link, merge strategy, build validation) | Repository settings, defined here as code | Platform team through a reviewed pull request |
| Environments and approval checks | Azure DevOps environments (`dev`, `staging`, `prod`) | Platform team; approvers are named groups, not individuals |
| Service connections | Project settings, one per environment, least privilege | Platform team; pipelines request access, an admin authorizes |
| Agent pools | Organization settings; Microsoft-hosted for dev, self-hosted inside the network for prod | Platform team |
| Pipeline templates | Shared template repository (see `azure-devops-pipeline-templates`) | Platform team; consumers pin a version |
| Artifacts and feeds | Azure Artifacts, one feed per ecosystem | Platform team |

## Principles

1. **Policy as code, reviewed like code.** A change to a rule is a pull request with an approver, not a click.
2. **Dry-run first.** The tool prints the exact `az` commands before anything runs. `--apply` is explicit.
3. **Production needs a human.** Approvals live on the `prod` environment and cannot be bypassed by a pipeline author.
4. **Separate the identity from the person.** Each environment has its own service connection with only the roles it needs.
5. **Evidence over assertion.** Build validation proves the pipeline passed; a reviewer count proves a person looked.

## Limits of this repository

- It creates branch policies only. Environments, approval checks, service connections and pools are described here but are configured in Azure DevOps (or with the REST API) outside this code.
- It never edits or deletes existing policies, so re-running can duplicate policies. List current policies with `az repos policy list` first.
- Flag names follow the Azure DevOps CLI extension; confirm with `az repos policy <type> create --help` for your extension version.
