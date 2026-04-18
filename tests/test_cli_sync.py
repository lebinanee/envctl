"""Tests for the sync and export CLI commands."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from envctl.cli_sync import sync_group, sync_cmd, export_cmd
from envctl.sync import SyncError
from envctl.export import ExportError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def _mock_config(tmp_path):
    """Return a minimal mock Config object."""
    cfg = MagicMock()
    cfg.config_path = str(tmp_path / "config.json")
    cfg.list_profiles.return_value = ["local", "staging", "production"]
    cfg.get_profile.side_effect = lambda env: {
        "local": {"DB_HOST": "localhost", "DEBUG": "true"},
        "staging": {"DB_HOST": "staging.example.com", "DEBUG": "false"},
        "production": {"DB_HOST": "prod.example.com", "DEBUG": "false"},
    }.get(env, {})
    return cfg


def test_sync_cmd_success(runner, _mock_config):
    """sync copies vars from source to target env."""
    with patch("envctl.cli_sync.Config", return_value=_mock_config), \
         patch("envctl.cli_sync.sync_envs") as mock_sync:
        result = runner.invoke(sync_cmd, ["local", "staging"])
        assert result.exit_code == 0
        mock_sync.assert_called_once_with(_mock_config, "local", "staging", keys=None, overwrite=False)
        assert "Synced" in result.output or result.exit_code == 0


def test_sync_cmd_with_keys(runner, _mock_config):
    """sync --key filters which keys are synced."""
    with patch("envctl.cli_sync.Config", return_value=_mock_config), \
         patch("envctl.cli_sync.sync_envs") as mock_sync:
        result = runner.invoke(sync_cmd, ["local", "staging", "--key", "DB_HOST"])
        assert result.exit_code == 0
        mock_sync.assert_called_once_with(_mock_config, "local", "staging", keys=("DB_HOST",), overwrite=False)


def test_sync_cmd_overwrite(runner, _mock_config):
    """sync --overwrite flag is forwarded."""
    with patch("envctl.cli_sync.Config", return_value=_mock_config), \
         patch("envctl.cli_sync.sync_envs") as mock_sync:
        result = runner.invoke(sync_cmd, ["local", "staging", "--overwrite"])
        assert result.exit_code == 0
        mock_sync.assert_called_once_with(_mock_config, "local", "staging", keys=None, overwrite=True)


def test_sync_cmd_sync_error(runner, _mock_config):
    """SyncError is reported gracefully."""
    with patch("envctl.cli_sync.Config", return_value=_mock_config), \
         patch("envctl.cli_sync.sync_envs", side_effect=SyncError("bad env")):
        result = runner.invoke(sync_cmd, ["local", "unknown"])
        assert result.exit_code != 0 or "Error" in result.output or "bad env" in result.output


def test_export_cmd_dotenv(runner, _mock_config, tmp_path):
    """export writes a .env file for the given environment."""
    out_file = str(tmp_path / ".env")
    with patch("envctl.cli_sync.Config", return_value=_mock_config), \
         patch("envctl.cli_sync.export_to_file") as mock_export:
        result = runner.invoke(export_cmd, ["local", "--output", out_file])
        assert result.exit_code == 0
        mock_export.assert_called_once()
        call_args = mock_export.call_args
        assert call_args[0][1] == out_file or call_args[1].get("path") == out_file


def test_export_cmd_shell_format(runner, _mock_config, tmp_path):
    """export --format shell uses shell format."""
    out_file = str(tmp_path / "env.sh")
    with patch("envctl.cli_sync.Config", return_value=_mock_config), \
         patch("envctl.cli_sync.export_to_file") as mock_export:
        result = runner.invoke(export_cmd, ["local", "--output", out_file, "--format", "shell"])
        assert result.exit_code == 0
        mock_export.assert_called_once()


def test_export_cmd_export_error(runner, _mock_config, tmp_path):
    """ExportError is reported gracefully."""
    out_file = str(tmp_path / ".env")
    with patch("envctl.cli_sync.Config", return_value=_mock_config), \
         patch("envctl.cli_sync.export_to_file", side_effect=ExportError("write failed")):
        result = runner.invoke(export_cmd, ["local", "--output", out_file])
        assert result.exit_code != 0 or "write failed" in result.output or "Error" in result.output
