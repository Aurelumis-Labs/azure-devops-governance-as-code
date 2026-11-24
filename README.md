# azure-devops-governance-as-code

Define Azure DevOps branch policies in a YAML file, review the exact `az` commands in a dry run, then apply them. A small, tested Python tool plus a governance model for platform teams.

> Status: reference project with synthetic names. The command builder is unit-tested; applying policies against a live Azure DevOps organization has not been exercised here. Dry-run is the default.

## What this demonstrates

- **Governance as code:** reviewers, comment resolution, linked work items, merge strategy and build validation defined in one file.
- **Safe by default:** prints commands and runs nothing unless `--apply` is passed; validates the definition and rejects bad values.
- **Platform-owner thinking:** [docs/governance-model.md](docs/governance-model.md) describes who controls branch policies, environments, approvals, service connections, agent pools and templates.

## Use it

```bash
pip install -r requirements.txt
cp config/governance.example.yaml config/governance.yaml    # edit for your project
python -m governance config/governance.yaml                  # dry run: prints az commands
az login && az extension add --name azure-devops
python -m governance config/governance.yaml --apply          # creates the policies
python -m pytest -q                                          # run the tests
```

## Definition file

```yaml
organization: https://dev.azure.com/contoso
project: Contoso
repositories:
  - name: contoso-api
    branches:
      - name: main
        policies:
          min_reviewers: 2
          require_comment_resolution: true
          require_work_item_link: true
          merge_strategy: squash
          build_validation:
            - display_name: contoso-api-ci
              pipeline_id: 12
```

## Decision record

[ADR-0008](docs/adr/0008-governance-as-code-dry-run-default.md) explains why policies are defined as code, why the tool is dry-run by default, and why it only creates policies.

## Limits

Creates policies only; it does not update or delete existing ones, so check `az repos policy list` before applying. See the model document for what is out of scope.

## License

MIT
