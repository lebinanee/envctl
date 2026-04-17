"""Tests for envctl.sync module."""

import pytest
from unittest.mock import MagicMock
from envctl.sync import sync_envs, diff_envs, SyncError


def make_config(profiles):
    cfg = MagicMock()
    cfg.get_profile = lambda env: dict(profiles.get(env, {}))
    captured = {}

    def set_profile(env, data):
        captured[env] = data

    cfg.set_profile.side_effect = set_profile
    cfg._captured = captured
    return cfg


def test_diff_envs_added():
    result = diff_envs({"A": "1", "B": "2"}, {"A": "1"})
    assert result["added"] == {"B": "2"}
    assert result["changed"] == {}
    assert result["removed"] == {}


def test_diff_envs_changed():
    result = diff_envs({"A": "new"}, {"A": "old"})
    assert result["changed"] == {"A": {"from": "old", "to": "new"}}


def test_diff_envs_removed():
    result = diff_envs({}, {"X": "1"})
    assert result["removed"] == {"X": "1"}


def test_sync_applies_changes():
    cfg = make_config({"local": {"DB": "localhost"}, "staging": {}})
    changes = sync_envs(cfg, "local", "staging")
    assert changes["added"] == {"DB": "localhost"}
    cfg.save.assert_called_once()
    assert cfg._captured["staging"]["DB"] == "localhost"


def test_sync_dry_run_no_save():
    cfg = make_config({"local": {"KEY": "val"}, "staging": {}})
    changes = sync_envs(cfg, "local", "staging", dry_run=True)
    assert changes["added"] == {"KEY": "val"}
    cfg.save.assert_not_called()


def test_sync_specific_keys():
    cfg = make_config({"local": {"A": "1", "B": "2"}, "staging": {}})
    sync_envs(cfg, "local", "staging", keys=["A"])
    assert cfg._captured["staging"] == {"A": "1"}


def test_sync_invalid_env():
    cfg = make_config({})
    with pytest.raises(SyncError, match="Unknown environment"):
        sync_envs(cfg, "local", "unknown")


def test_sync_same_env_raises():
    cfg = make_config({"local": {}})
    with pytest.raises(SyncError, match="must differ"):
        sync_envs(cfg, "local", "local")


def test_sync_missing_keys_raises():
    cfg = make_config({"local": {"A": "1"}, "staging": {}})
    with pytest.raises(SyncError, match="Keys not found"):
        sync_envs(cfg, "local", "staging", keys=["MISSING"])
