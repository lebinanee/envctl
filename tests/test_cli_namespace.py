"""Tests for envctl.cli_namespace CLI commands."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_namespace import namespace_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _mock_config(profile_name: str = "local", profile: dict | None = None):
    cfg = MagicMock()
    cfg.get_active_env.return_value = profile_name
    cfg.get_profile.return_value = profile if profile is not None else {}
    return cfg


def test_list_cmd_shows_namespaces(runner):
    profile = {"DB__HOST": "localhost", "CACHE__URL": "redis://"}
    cfg = _mock_config(profile=profile)
    with patch("envctl.cli_namespace.Config", return_value=cfg):
        result = runner.invoke(namespace_group, ["list"])
    assert result.exit_code == 0
    assert "CACHE" in result.output
    assert "DB" in result.output


def test_list_cmd_empty_profile(runner):
    cfg = _mock_config(profile={})
    with patch("envctl.cli_namespace.Config", return_value=cfg):
        result = runner.invoke(namespace_group, ["list"])
    assert result.exit_code == 0
    assert "No namespaces" in result.output


def test_show_cmd_displays_keys(runner):
    profile = {"DB__HOST": "localhost", "DB__PORT": "5432", "OTHER": "x"}
    cfg = _mock_config(profile=profile)
    with patch("envctl.cli_namespace.Config", return_value=cfg):
        result = runner.invoke(namespace_group, ["show", "DB"])
    assert result.exit_code == 0
    assert "DB__HOST=localhost" in result.output
    assert "DB__PORT=5432" in result.output
    assert "OTHER" not in result.output


def test_show_cmd_unknown_namespace(runner):
    cfg = _mock_config(profile={"FOO": "bar"})
    with patch("envctl.cli_namespace.Config", return_value=cfg):
        result = runner.invoke(namespace_group, ["show", "GHOST"])
    assert result.exit_code == 0
    assert "No keys found" in result.output


def test_delete_cmd_removes_keys(runner):
    profile = {"DB__HOST": "localhost", "DB__PORT": "5432"}
    cfg = _mock_config(profile=profile)
    with patch("envctl.cli_namespace.Config", return_value=cfg):
        result = runner.invoke(namespace_group, ["delete", "DB"])
    assert result.exit_code == 0
    assert "Removed 2" in result.output
    cfg.save.assert_called_once()


def test_rename_cmd_success(runner):
    profile = {"DB__HOST": "localhost"}
    cfg = _mock_config(profile=profile)
    with patch("envctl.cli_namespace.Config", return_value=cfg):
        result = runner.invoke(namespace_group, ["rename", "DB", "DATABASE"])
    assert result.exit_code == 0
    assert "Renamed 1" in result.output
    cfg.save.assert_called_once()


def test_rename_cmd_invalid_new_name(runner):
    profile = {"DB__HOST": "localhost"}
    cfg = _mock_config(profile=profile)
    with patch("envctl.cli_namespace.Config", return_value=cfg):
        result = runner.invoke(namespace_group, ["rename", "DB", "123bad"])
    assert result.exit_code != 0
    assert "Error" in result.output
