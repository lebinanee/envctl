"""Tests for envctl.cli_import CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envctl.cli_import import import_group


@pytest.fixture
def runner():
    return CliRunner()


def _mock_config(profile=None):
    cfg = MagicMock()
    cfg.get_profile = lambda env: dict(profile or {})
    cfg.set_var = MagicMock()
    cfg.save = MagicMock()
    return cfg


def test_import_cmd_success(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    cfg = _mock_config()
    with patch("envctl.cli_import.Config", return_value=cfg):
        result = runner.invoke(import_group, ["file", "local", str(env_file)])
    assert result.exit_code == 0
    assert "Added" in result.output
    assert "FOO" in result.output


def test_import_cmd_dry_run(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    cfg = _mock_config()
    with patch("envctl.cli_import.Config", return_value=cfg):
        result = runner.invoke(import_group, ["file", "local", str(env_file), "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    cfg.save.assert_not_called()


def test_import_cmd_skips_existing(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    cfg = _mock_config({"FOO": "old"})
    with patch("envctl.cli_import.Config", return_value=cfg):
        result = runner.invoke(import_group, ["file", "local", str(env_file)])
    assert result.exit_code == 0
    assert "Skipped" in result.output


def test_import_cmd_missing_file(runner):
    with patch("envctl.cli_import.Config", return_value=_mock_config()):
        result = runner.invoke(import_group, ["file", "local", "/no/such/file.env"])
    assert result.exit_code != 0
    assert "File not found" in result.output


def test_import_cmd_no_vars(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# only comments\n")
    cfg = _mock_config()
    with patch("envctl.cli_import.Config", return_value=cfg):
        result = runner.invoke(import_group, ["file", "local", str(env_file)])
    assert result.exit_code == 0
    assert "No variables imported" in result.output
