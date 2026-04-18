"""Tests for envctl.snapshot."""

import pytest
from unittest.mock import MagicMock
from envctl.snapshot import (
    take_snapshot,
    list_snapshots,
    restore_snapshot,
    delete_snapshot,
    SnapshotError,
)


@pytest.fixture
def snap_file(tmp_path):
    return str(tmp_path / "snapshots.json")


def make_config(profiles: dict):
    config = MagicMock()
    config.get_profile = lambda env: profiles.get(env)
    config.set_profile = MagicMock()
    config.save = MagicMock()
    return config


def test_take_snapshot_creates_entry(snap_file):
    config = make_config({"local": {"KEY": "val"}})
    entry = take_snapshot(config, "local", path=snap_file)
    assert entry["env"] == "local"
    assert entry["vars"] == {"KEY": "val"}
    assert "timestamp" in entry


def test_take_snapshot_with_label(snap_file):
    config = make_config({"staging": {"A": "1"}})
    entry = take_snapshot(config, "staging", label="pre-deploy", path=snap_file)
    assert entry["label"] == "pre-deploy"


def test_take_snapshot_no_profile_raises(snap_file):
    config = make_config({})
    with pytest.raises(SnapshotError, match="no variables"):
        take_snapshot(config, "prod", path=snap_file)


def test_list_snapshots_empty(snap_file):
    assert list_snapshots(path=snap_file) == []


def test_list_snapshots_filtered(snap_file):
    config = make_config({"local": {"X": "1"}, "staging": {"Y": "2"}})
    take_snapshot(config, "local", path=snap_file)
    take_snapshot(config, "staging", path=snap_file)
    result = list_snapshots(env="local", path=snap_file)
    assert len(result) == 1
    assert result[0]["env"] == "local"


def test_restore_snapshot(snap_file):
    config = make_config({"local": {"KEY": "hello"}})
    take_snapshot(config, "local", path=snap_file)
    restore_snapshot(config, 0, path=snap_file)
    config.set_profile.assert_called_once_with("local", {"KEY": "hello"})
    config.save.assert_called_once()


def test_restore_invalid_index_raises(snap_file):
    config = make_config({"local": {"A": "1"}})
    take_snapshot(config, "local", path=snap_file)
    with pytest.raises(SnapshotError, match="out of range"):
        restore_snapshot(config, 5, path=snap_file)


def test_delete_snapshot(snap_file):
    config = make_config({"local": {"A": "1"}})
    take_snapshot(config, "local", path=snap_file)
    take_snapshot(config, "local", path=snap_file)
    delete_snapshot(0, path=snap_file)
    assert len(list_snapshots(path=snap_file)) == 1


def test_delete_invalid_index_raises(snap_file):
    with pytest.raises(SnapshotError):
        delete_snapshot(0, path=snap_file)
