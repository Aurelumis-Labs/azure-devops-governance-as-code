import pytest
import yaml

from governance.policies import ConfigError, build_commands

CONFIG = yaml.safe_load("""
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
""")


def joined(cmds):
    return [c.shell() for c in cmds]


def test_builds_one_command_per_policy():
    assert len(build_commands(CONFIG)) == 5


def test_reviewer_policy_flags():
    cmd = joined(build_commands(CONFIG))[0]
    assert "approver-count create" in cmd
    assert "--minimum-approver-count 2" in cmd
    assert "--reset-on-source-push true" in cmd


def test_squash_only():
    cmd = next(c for c in joined(build_commands(CONFIG)) if "merge-strategy" in c)
    assert "--allow-squash true" in cmd
    assert "--allow-rebase true" not in cmd


def test_dry_run_uses_placeholder_repo_id():
    assert "<id:contoso-api>" in joined(build_commands(CONFIG))[0]


def test_real_repo_id_is_used_when_given():
    cmds = build_commands(CONFIG, {"contoso-api": "abc-123"})
    assert "abc-123" in cmds[0].shell()


def test_bad_merge_strategy_rejected():
    bad = yaml.safe_load(yaml.safe_dump(CONFIG))
    bad["repositories"][0]["branches"][0]["policies"]["merge_strategy"] = "cherry"
    with pytest.raises(ConfigError):
        build_commands(bad)


def test_zero_reviewers_rejected():
    bad = yaml.safe_load(yaml.safe_dump(CONFIG))
    bad["repositories"][0]["branches"][0]["policies"]["min_reviewers"] = 0
    with pytest.raises(ConfigError):
        build_commands(bad)


def test_missing_key_rejected():
    with pytest.raises(ConfigError):
        build_commands({"organization": "x"})
