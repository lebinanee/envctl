"""CLI tests for snapshot commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envctl.cli_snapshot import snapshot_group


@pytest.fixture
def runner():
    return CliRunner()


def _mock_config(profiles=None):
    config = MagicMock()
    config.get_profile = lambda env: (profiles or {}).get(env)
    config.set_profile = MagicMock()
    config.save = MagicMock()
    return config


def test_take_cmd_success(runner, tmp_path):
    snap_file = str(tmp_path / "s.json")
    config = _mock_config({"local": {"K": "v"}})
    with patch("envctl.cli_snapshot.Config", return_value=config), \
         patch("envctl.cli_snapshot.take_snapshot") as mock_take:
        mock_take.return_value = {"env": "local", "timestamp": "2024-01-01T00:00:00+00:00", "label": ""}
        result = runner.invoke(snapshot_group, ["take", "local"])
    assert result.exit_code == 0
    assert "Snapshot taken" in result.output


def test_take_cmd_with_label(runner):
    config = _mock_config({"staging": {"A": "1"}})
    with patch("envctl.cli_snapshot.Config", return_value=config), \
         patch("envctl.cli_snapshot.take_snapshot") as mock_take:
        mock_take.return_value = {"env": "staging", "timestamp": "2024-01-01T00:00:00+00:00", "label": "v2"}
        result = runner.invoke(snapshot_group, ["take", "staging", "--label", "v2"])
    assert "Label: v2" in result.output


def test_list_cmd_empty(runner):
    with patch("envctl.cli_snapshot.list_snapshots", return_value=[]):
        result = runner.invoke(snapshot_group, ["list"])
    assert "No snapshots" in result.output


def test_list_cmd_shows_entries(runner):
    snapshots = [{"env": "local", "timestamp": "2024-01-01T00:00:00+00:00", "label": "", "vars": {"A": "1"}}]
    with patch("envctl.cli_snapshot.list_snapshots", return_value=snapshots):
        result = runner.invoke(snapshot_group, ["list"])
    assert "local" in result.output


def test_restore_cmd_success(runner):
    config = _mock_config()
    with patch("envctl.cli_snapshot.Config", return_value=config), \
         patch("envctl.cli_snapshot.restore_snapshot") as mock_restore:
        mock_restore.return_value = {"env": "local", "timestamp": "2024-01-01T00:00:00+00:00"}
        result = runner.invoke(snapshot_group, ["restore", "0"])
    assert result.exit_code == 0
    assert "Restored" in result.output


def test_delete_cmd_success(runner):
    with patch("envctl.cli_snapshot.delete_snapshot") as mock_del:
        result = runner.invoke(snapshot_group, ["delete", "0"])
    assert result.exit_code == 0
    assert "deleted" in result.output
