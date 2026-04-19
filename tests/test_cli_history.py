import json
import time
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envctl.cli_history import history_group
from envctl.history import HistoryEntry


@pytest.fixture
def runner():
    return CliRunner()


def _entry(profile="local", key="API_KEY", old=None, new="abc", action="set"):
    return HistoryEntry(profile=profile, key=key, old_value=old,
                        new_value=new, action=action, timestamp=time.time())


def test_log_empty(runner):
    with patch("envctl.cli_history.get_history", return_value=[]):
        result = runner.invoke(history_group, ["log"])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_log_shows_entries(runner):
    entries = [_entry(action="set"), _entry(key="DB_URL", action="delete", new=None, old="x")]
    with patch("envctl.cli_history.get_history", return_value=entries):
        result = runner.invoke(history_group, ["log"])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "DB_URL" in result.output


def test_log_filter_profile(runner):
    with patch("envctl.cli_history.get_history", return_value=[]) as mock_gh:
        runner.invoke(history_group, ["log", "--profile", "prod"])
        mock_gh.assert_called_once_with(profile="prod", key=None)


def test_clear_cmd(runner):
    with patch("envctl.cli_history.clear_history") as mock_clear:
        result = runner.invoke(history_group, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert "cleared" in result.output
    mock_clear.assert_called_once()
