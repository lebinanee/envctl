"""Tests for CLI TTL commands."""
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from envctl.cli_ttl import ttl_group
from envctl.ttl import TTLEntry, TTLError
from datetime import datetime, timedelta


@pytest.fixture
def runner():
    return CliRunner()


import pytest


def _entry(key="API_KEY", profile="local", delta=3600):
    expires_at = (datetime.utcnow() + timedelta(seconds=delta)).isoformat()
    return TTLEntry(key, profile, expires_at)


def _mock_config(monkeypatch, profile_data=None):
    cfg = MagicMock()
    cfg.path = "/fake/config.json"
    cfg.get_profile.return_value = profile_data or {"API_KEY": "secret"}
    monkeypatch.setattr("envctl.cli_ttl.Config", lambda: cfg)
    return cfg


def test_set_cmd_success(runner, monkeypatch):
    _mock_config(monkeypatch)
    entry = _entry()
    with patch("envctl.cli_ttl.ttl_mod.set_ttl", return_value=entry):
        result = runner.invoke(ttl_group, ["set", "local", "API_KEY", "--seconds", "3600"])
    assert result.exit_code == 0
    assert "expires at" in result.output


def test_set_cmd_error(runner, monkeypatch):
    _mock_config(monkeypatch)
    with patch("envctl.cli_ttl.ttl_mod.set_ttl", side_effect=TTLError("not found")):
        result = runner.invoke(ttl_group, ["set", "local", "MISSING", "--seconds", "60"])
    assert "Error" in result.output


def test_get_cmd_no_ttl(runner, monkeypatch):
    _mock_config(monkeypatch)
    with patch("envctl.cli_ttl.ttl_mod.get_ttl", return_value=None):
        result = runner.invoke(ttl_group, ["get", "local", "API_KEY"])
    assert "No TTL" in result.output


def test_get_cmd_with_ttl(runner, monkeypatch):
    _mock_config(monkeypatch)
    entry = _entry()
    with patch("envctl.cli_ttl.ttl_mod.get_ttl", return_value=entry):
        result = runner.invoke(ttl_group, ["get", "local", "API_KEY"])
    assert "active" in result.output


def test_list_cmd_empty(runner, monkeypatch):
    _mock_config(monkeypatch)
    with patch("envctl.cli_ttl.ttl_mod.list_ttls", return_value=[]):
        result = runner.invoke(ttl_group, ["list", "local"])
    assert "No TTLs" in result.output


def test_purge_cmd_removes(runner, monkeypatch):
    _mock_config(monkeypatch)
    with patch("envctl.cli_ttl.ttl_mod.purge_expired", return_value=["OLD_KEY"]):
        result = runner.invoke(ttl_group, ["purge", "local"])
    assert "OLD_KEY" in result.output


def test_purge_cmd_nothing(runner, monkeypatch):
    _mock_config(monkeypatch)
    with patch("envctl.cli_ttl.ttl_mod.purge_expired", return_value=[]):
        result = runner.invoke(ttl_group, ["purge", "local"])
    assert "No expired" in result.output
