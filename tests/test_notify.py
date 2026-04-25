"""Tests for envctl.notify."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envctl.notify import (
    NotifyError,
    NotifyRule,
    add_rule,
    remove_rule,
    list_rules,
    matching_rules,
    _rules_path,
)


def make_config(tmp_path: Path, envs=None):
    cfg_file = tmp_path / "envctl.json"
    cfg_file.write_text(json.dumps({"active": "local", "profiles": {}}))
    mock = MagicMock()
    mock.path = str(cfg_file)
    mock.list_envs.return_value = envs or ["local", "staging", "production"]
    return mock


def test_add_rule_success(tmp_path):
    cfg = make_config(tmp_path)
    rule = add_rule(cfg, "local", "https://hooks.example.com/abc")
    assert rule.profile == "local"
    assert rule.webhook_url == "https://hooks.example.com/abc"
    assert rule.keys == []


def test_add_rule_with_keys(tmp_path):
    cfg = make_config(tmp_path)
    rule = add_rule(cfg, "staging", "https://hooks.example.com/xyz", keys=["API_KEY", "DB_URL"])
    assert rule.keys == ["API_KEY", "DB_URL"]


def test_add_rule_with_label(tmp_path):
    cfg = make_config(tmp_path)
    rule = add_rule(cfg, "local", "https://hooks.example.com/abc", label="slack-alerts")
    assert rule.label == "slack-alerts"


def test_add_rule_missing_profile_raises(tmp_path):
    cfg = make_config(tmp_path, envs=["local"])
    with pytest.raises(NotifyError, match="staging"):
        add_rule(cfg, "staging", "https://hooks.example.com/abc")


def test_add_rule_persists(tmp_path):
    cfg = make_config(tmp_path)
    add_rule(cfg, "local", "https://hooks.example.com/1")
    add_rule(cfg, "local", "https://hooks.example.com/2")
    rules = list_rules(cfg)
    assert len(rules) == 2


def test_remove_rule_success(tmp_path):
    cfg = make_config(tmp_path)
    add_rule(cfg, "local", "https://hooks.example.com/abc")
    removed = remove_rule(cfg, "local", "https://hooks.example.com/abc")
    assert removed is True
    assert list_rules(cfg) == []


def test_remove_rule_not_found(tmp_path):
    cfg = make_config(tmp_path)
    removed = remove_rule(cfg, "local", "https://hooks.example.com/missing")
    assert removed is False


def test_list_rules_filter_by_profile(tmp_path):
    cfg = make_config(tmp_path)
    add_rule(cfg, "local", "https://hooks.example.com/1")
    add_rule(cfg, "staging", "https://hooks.example.com/2")
    local_rules = list_rules(cfg, profile="local")
    assert len(local_rules) == 1
    assert local_rules[0].profile == "local"


def test_matching_rules_all_keys(tmp_path):
    cfg = make_config(tmp_path)
    add_rule(cfg, "local", "https://hooks.example.com/all")
    matches = matching_rules(cfg, "local", ["ANY_KEY"])
    assert len(matches) == 1


def test_matching_rules_specific_key_match(tmp_path):
    cfg = make_config(tmp_path)
    add_rule(cfg, "local", "https://hooks.example.com/abc", keys=["API_KEY"])
    matches = matching_rules(cfg, "local", ["API_KEY", "DB_URL"])
    assert len(matches) == 1


def test_matching_rules_specific_key_no_match(tmp_path):
    cfg = make_config(tmp_path)
    add_rule(cfg, "local", "https://hooks.example.com/abc", keys=["SECRET"])
    matches = matching_rules(cfg, "local", ["API_KEY"])
    assert matches == []


def test_notify_rule_roundtrip():
    rule = NotifyRule(profile="local", keys=["K"], webhook_url="https://x.com", label="test")
    assert NotifyRule.from_dict(rule.to_dict()) == rule
