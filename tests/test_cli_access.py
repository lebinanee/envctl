"""Tests for envctl.cli_access."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from envctl.cli_access import access_group


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config(profiles=None):
    cfg = MagicMock()
    cfg.list_profiles.return_value = profiles or ["local", "staging"]
    return cfg


def test_grant_cmd_success(runner, tmp_path):
    cfg = _mock_config()
    with patch("envctl.cli_access.set_access") as mock_set:
        result = runner.invoke(
            access_group, ["grant", "local", "dev", "DB_URL", "API_KEY"],
            obj=cfg,
        )
    assert result.exit_code == 0
    assert "Granted read access" in result.output
    mock_set.assert_called_once_with(cfg, "local", "dev", ["DB_URL", "API_KEY"], "read")


def test_grant_cmd_write_mode(runner):
    cfg = _mock_config()
    with patch("envctl.cli_access.set_access") as mock_set:
        result = runner.invoke(
            access_group, ["grant", "staging", "admin", "SECRET", "--mode", "write"],
            obj=cfg,
        )
    assert result.exit_code == 0
    assert "write" in result.output
    mock_set.assert_called_once_with(cfg, "staging", "admin", ["SECRET"], "write")


def test_grant_cmd_error(runner):
    cfg = _mock_config()
    from envctl.access import AccessError
    with patch("envctl.cli_access.set_access", side_effect=AccessError("bad profile")):
        result = runner.invoke(
            access_group, ["grant", "nope", "dev", "KEY"], obj=cfg
        )
    assert "Error" in result.output


def test_revoke_cmd_success(runner):
    cfg = _mock_config()
    with patch("envctl.cli_access.revoke_access", return_value=True) as mock_rev:
        result = runner.invoke(
            access_group, ["revoke", "local", "dev"], obj=cfg
        )
    assert result.exit_code == 0
    assert "Revoked" in result.output
    mock_rev.assert_called_once_with(cfg, "local", "dev", None)


def test_revoke_cmd_not_found(runner):
    cfg = _mock_config()
    with patch("envctl.cli_access.revoke_access", return_value=False):
        result = runner.invoke(
            access_group, ["revoke", "local", "ghost"], obj=cfg
        )
    assert "No access entry" in result.output


def test_check_cmd_allowed(runner):
    cfg = _mock_config()
    with patch("envctl.cli_access.check_access", return_value=True):
        result = runner.invoke(
            access_group, ["check", "local", "dev", "DB_URL"], obj=cfg
        )
    assert "ALLOWED" in result.output


def test_check_cmd_denied(runner):
    cfg = _mock_config()
    with patch("envctl.cli_access.check_access", return_value=False):
        result = runner.invoke(
            access_group, ["check", "local", "dev", "SECRET"], obj=cfg
        )
    assert "DENIED" in result.output


def test_list_cmd_empty(runner):
    cfg = _mock_config()
    with patch("envctl.cli_access.list_access", return_value={}):
        result = runner.invoke(access_group, ["list", "local"], obj=cfg)
    assert "No access rules" in result.output


def test_list_cmd_shows_rules(runner):
    cfg = _mock_config()
    acl = {"admin": {"write": ["DB_PASS"]}, "viewer": {"read": ["APP_URL"]}}
    with patch("envctl.cli_access.list_access", return_value=acl):
        result = runner.invoke(access_group, ["list", "staging"], obj=cfg)
    assert "admin" in result.output
    assert "viewer" in result.output
