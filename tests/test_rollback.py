"""Tests for envctl.rollback."""
import pytest
from unittest.mock import patch, MagicMock
from envctl.rollback import rollback_profile, RollbackError


def make_config(profiles=None):
    cfg = MagicMock()
    _profiles = dict(profiles or {})
    cfg.get_profile = lambda p: dict(_profiles.get(p, {}))
    cfg.set_profile = lambda p, v: _profiles.update({p: v})
    cfg.save = MagicMock()
    return cfg, _profiles


SNAP_ID = "snap-001"


def _snapshots(profile_data):
    return [{"id": SNAP_ID, "profiles": {"local": profile_data}}]


def test_rollback_adds_new_keys():
    cfg, profiles = make_config({"local": {"A": "1"}})
    with patch("envctl.rollback.list_snapshots", return_value=_snapshots({"A": "1", "B": "2"})):
        diff = rollback_profile(cfg, "local", SNAP_ID)
    assert "B" in diff["added"]
    assert diff["changed"] == {}
    assert diff["removed"] == {}


def test_rollback_removes_keys():
    cfg, profiles = make_config({"local": {"A": "1", "B": "2"}})
    with patch("envctl.rollback.list_snapshots", return_value=_snapshots({"A": "1"})):
        diff = rollback_profile(cfg, "local", SNAP_ID)
    assert "B" in diff["removed"]


def test_rollback_changed_keys():
    cfg, profiles = make_config({"local": {"A": "old"}})
    with patch("envctl.rollback.list_snapshots", return_value=_snapshots({"A": "new"})):
        diff = rollback_profile(cfg, "local", SNAP_ID)
    assert diff["changed"] == {"A": "new"}


def test_rollback_no_changes():
    cfg, _ = make_config({"local": {"A": "1"}})
    with patch("envctl.rollback.list_snapshots", return_value=_snapshots({"A": "1"})):
        diff = rollback_profile(cfg, "local", SNAP_ID)
    assert not any(diff.values())


def test_rollback_missing_snapshot_raises():
    cfg, _ = make_config({"local": {}})
    with patch("envctl.rollback.list_snapshots", return_value=[]):
        with pytest.raises(RollbackError, match="not found"):
            rollback_profile(cfg, "local", "bad-id")


def test_rollback_profile_not_in_snapshot_raises():
    cfg, _ = make_config({"local": {}})
    with patch("envctl.rollback.list_snapshots", return_value=[{"id": SNAP_ID, "profiles": {}}]):
        with pytest.raises(RollbackError, match="not present"):
            rollback_profile(cfg, "local", SNAP_ID)


def test_dry_run_does_not_save():
    cfg, _ = make_config({"local": {"A": "1"}})
    with patch("envctl.rollback.list_snapshots", return_value=_snapshots({"A": "2"})):
        rollback_profile(cfg, "local", SNAP_ID, dry_run=True)
    cfg.save.assert_not_called()
