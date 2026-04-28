"""Tests for envctl.cli_freeze CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envctl.cli_freeze import freeze_group


@pytest.fixture
def runner():
    return CliRunner()


def _mock_config(tmp_path, frozen=None):
    config = MagicMock()
    config.config_dir = str(tmp_path)
    config.get_active_env.return_value = "default"
    config.get.return_value = {"local": {}, "staging": {}}
    return config


def test_add_cmd_success(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_freeze.Config", return_value=cfg), \
         patch("envctl.cli_freeze.freeze_profile", return_value=True) as mock_freeze:
        result = runner.invoke(freeze_group, ["add", "local"])
    assert result.exit_code == 0
    assert "frozen" in result.output
    mock_freeze.assert_called_once_with(cfg, "local")


def test_add_cmd_already_frozen(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_freeze.Config", return_value=cfg), \
         patch("envctl.cli_freeze.freeze_profile", return_value=False):
        result = runner.invoke(freeze_group, ["add", "local"])
    assert result.exit_code == 0
    assert "already frozen" in result.output


def test_add_cmd_error(runner, tmp_path):
    from envctl.freeze import FreezeError
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_freeze.Config", return_value=cfg), \
         patch("envctl.cli_freeze.freeze_profile", side_effect=FreezeError("bad")):
        result = runner.invoke(freeze_group, ["add", "ghost"])
    assert result.exit_code != 0
    assert "bad" in result.output


def test_remove_cmd_success(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_freeze.Config", return_value=cfg), \
         patch("envctl.cli_freeze.unfreeze_profile", return_value=True):
        result = runner.invoke(freeze_group, ["remove", "local"])
    assert result.exit_code == 0
    assert "unfrozen" in result.output


def test_remove_cmd_not_frozen(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_freeze.Config", return_value=cfg), \
         patch("envctl.cli_freeze.unfreeze_profile", return_value=False):
        result = runner.invoke(freeze_group, ["remove", "local"])
    assert result.exit_code == 0
    assert "not frozen" in result.output


def test_status_cmd_frozen(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_freeze.Config", return_value=cfg), \
         patch("envctl.cli_freeze.is_frozen", return_value=True):
        result = runner.invoke(freeze_group, ["status", "local"])
    assert result.exit_code == 0
    assert "frozen" in result.output


def test_list_cmd_empty(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_freeze.Config", return_value=cfg), \
         patch("envctl.cli_freeze.list_frozen", return_value=[]):
        result = runner.invoke(freeze_group, ["list"])
    assert result.exit_code == 0
    assert "No profiles" in result.output


def test_list_cmd_shows_profiles(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_freeze.Config", return_value=cfg), \
         patch("envctl.cli_freeze.list_frozen", return_value=["local", "staging"]):
        result = runner.invoke(freeze_group, ["list"])
    assert result.exit_code == 0
    assert "local" in result.output
    assert "staging" in result.output
