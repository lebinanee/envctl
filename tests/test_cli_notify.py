"""Tests for envctl.cli_notify CLI commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from envctl.cli_notify import notify_group
from envctl.notify import NotifyRule, NotifyError


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config(envs=None):
    cfg = MagicMock()
    cfg.list_envs.return_value = envs or ["local", "staging"]
    return cfg


def test_add_cmd_success(runner):
    cfg = _mock_config()
    rule = NotifyRule(profile="local", keys=[], webhook_url="https://hooks.example.com/abc")
    with patch("envctl.cli_notify.Config", return_value=cfg), \
         patch("envctl.cli_notify.add_rule", return_value=rule) as mock_add:
        result = runner.invoke(notify_group, ["add", "local", "https://hooks.example.com/abc"])
    assert result.exit_code == 0
    assert "local" in result.output
    assert "all keys" in result.output


def test_add_cmd_with_keys(runner):
    cfg = _mock_config()
    rule = NotifyRule(profile="local", keys=["API_KEY"], webhook_url="https://hooks.example.com/abc")
    with patch("envctl.cli_notify.Config", return_value=cfg), \
         patch("envctl.cli_notify.add_rule", return_value=rule):
        result = runner.invoke(
            notify_group,
            ["add", "local", "https://hooks.example.com/abc", "--key", "API_KEY"]
        )
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_add_cmd_error(runner):
    cfg = _mock_config()
    with patch("envctl.cli_notify.Config", return_value=cfg), \
         patch("envctl.cli_notify.add_rule", side_effect=NotifyError("Profile 'x' does not exist.")):
        result = runner.invoke(notify_group, ["add", "x", "https://hooks.example.com/abc"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_remove_cmd_success(runner):
    cfg = _mock_config()
    with patch("envctl.cli_notify.Config", return_value=cfg), \
         patch("envctl.cli_notify.remove_rule", return_value=True):
        result = runner.invoke(notify_group, ["remove", "local", "https://hooks.example.com/abc"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_cmd_not_found(runner):
    cfg = _mock_config()
    with patch("envctl.cli_notify.Config", return_value=cfg), \
         patch("envctl.cli_notify.remove_rule", return_value=False):
        result = runner.invoke(notify_group, ["remove", "local", "https://hooks.example.com/missing"])
    assert result.exit_code == 1


def test_list_cmd_empty(runner):
    cfg = _mock_config()
    with patch("envctl.cli_notify.Config", return_value=cfg), \
         patch("envctl.cli_notify.list_rules", return_value=[]):
        result = runner.invoke(notify_group, ["list"])
    assert result.exit_code == 0
    assert "No notification rules" in result.output


def test_list_cmd_shows_rules(runner):
    cfg = _mock_config()
    rules = [
        NotifyRule(profile="local", keys=["DB_URL"], webhook_url="https://hooks.example.com/1", label="db"),
        NotifyRule(profile="staging", keys=[], webhook_url="https://hooks.example.com/2"),
    ]
    with patch("envctl.cli_notify.Config", return_value=cfg), \
         patch("envctl.cli_notify.list_rules", return_value=rules):
        result = runner.invoke(notify_group, ["list"])
    assert result.exit_code == 0
    assert "DB_URL" in result.output
    assert "db" in result.output
    assert "staging" in result.output
