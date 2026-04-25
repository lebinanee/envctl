"""Tests for CLI checkpoint commands."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_checkpoint import checkpoint_group
from envctl.checkpoint import CheckpointError


@pytest.fixture
def runner():
    return CliRunner()


def _mock_config(profiles=None):
    cfg = MagicMock()
    cfg.path = "/fake/envctl.json"
    profiles = profiles or {}
    cfg.get_profile.side_effect = lambda p: profiles.get(p)
    return cfg


def test_create_cmd_success(runner):
    entry = {"name": "cp1", "profile": "local", "note": "", "timestamp": 1000.0, "vars": {}}
    with patch("envctl.cli_checkpoint.Config") as MockCfg, \
         patch("envctl.cli_checkpoint.create_checkpoint", return_value=entry) as mock_create:
        MockCfg.return_value = _mock_config({"local": {}})
        result = runner.invoke(checkpoint_group, ["create", "local", "cp1"])
    assert result.exit_code == 0
    assert "cp1" in result.output
    assert "local" in result.output


def test_create_cmd_with_note(runner):
    entry = {"name": "cp1", "profile": "local", "note": "release", "timestamp": 1000.0, "vars": {}}
    with patch("envctl.cli_checkpoint.Config"), \
         patch("envctl.cli_checkpoint.create_checkpoint", return_value=entry):
        result = runner.invoke(checkpoint_group, ["create", "local", "cp1", "--note", "release"])
    assert "release" in result.output


def test_create_cmd_error(runner):
    with patch("envctl.cli_checkpoint.Config"), \
         patch("envctl.cli_checkpoint.create_checkpoint", side_effect=CheckpointError("bad")):
        result = runner.invoke(checkpoint_group, ["create", "local", "cp1"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_list_cmd_empty(runner):
    with patch("envctl.cli_checkpoint.Config"), \
         patch("envctl.cli_checkpoint.list_checkpoints", return_value=[]):
        result = runner.invoke(checkpoint_group, ["list"])
    assert "No checkpoints" in result.output


def test_list_cmd_shows_entries(runner):
    entries = [
        {"profile": "local", "name": "cp1", "timestamp": 1700000000.0, "note": ""}
    ]
    with patch("envctl.cli_checkpoint.Config"), \
         patch("envctl.cli_checkpoint.list_checkpoints", return_value=entries):
        result = runner.invoke(checkpoint_group, ["list"])
    assert "cp1" in result.output
    assert "local" in result.output


def test_restore_cmd_success(runner):
    with patch("envctl.cli_checkpoint.Config"), \
         patch("envctl.cli_checkpoint.restore_checkpoint", return_value={"A": "1", "B": "2"}):
        result = runner.invoke(checkpoint_group, ["restore", "local", "cp1"])
    assert result.exit_code == 0
    assert "2 keys" in result.output


def test_delete_cmd_success(runner):
    with patch("envctl.cli_checkpoint.Config"), \
         patch("envctl.cli_checkpoint.delete_checkpoint", return_value=True):
        result = runner.invoke(checkpoint_group, ["delete", "local", "cp1"])
    assert "deleted" in result.output


def test_delete_cmd_not_found(runner):
    with patch("envctl.cli_checkpoint.Config"), \
         patch("envctl.cli_checkpoint.delete_checkpoint", return_value=False):
        result = runner.invoke(checkpoint_group, ["delete", "local", "ghost"])
    assert "not found" in result.output
