"""Tests for envctl.cli_rollback."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envctl.cli_rollback import rollback_group


@pytest.fixture
def runner():
    return CliRunner()


def _mock_config():
    cfg = MagicMock()
    return cfg


def test_apply_cmd_success(runner):
    diff = {"added": {"B": "2"}, "changed": {}, "removed": {}}
    with patch("envctl.cli_rollback.Config", return_value=_mock_config()), \
         patch("envctl.cli_rollback.rollback_profile", return_value=diff):
        result = runner.invoke(rollback_group, ["apply", "local", "snap-001"])
    assert result.exit_code == 0
    assert "ADD" in result.output


def test_apply_cmd_no_changes(runner):
    diff = {"added": {}, "changed": {}, "removed": {}}
    with patch("envctl.cli_rollback.Config", return_value=_mock_config()), \
         patch("envctl.cli_rollback.rollback_profile", return_value=diff):
        result = runner.invoke(rollback_group, ["apply", "local", "snap-001"])
    assert result.exit_code == 0
    assert "No changes" in result.output


def test_apply_cmd_dry_run(runner):
    diff = {"added": {}, "changed": {"A": "new"}, "removed": {}}
    with patch("envctl.cli_rollback.Config", return_value=_mock_config()), \
         patch("envctl.cli_rollback.rollback_profile", return_value=diff) as mock_rb:
        result = runner.invoke(rollback_group, ["apply", "local", "snap-001", "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    mock_rb.assert_called_once()
    _, kwargs = mock_rb.call_args
    assert kwargs.get("dry_run") is True or mock_rb.call_args[0][3] is True


def test_apply_cmd_error(runner):
    from envctl.rollback import RollbackError
    with patch("envctl.cli_rollback.Config", return_value=_mock_config()), \
         patch("envctl.cli_rollback.rollback_profile", side_effect=RollbackError("bad")):
        result = runner.invoke(rollback_group, ["apply", "local", "snap-bad"])
    assert result.exit_code != 0
    assert "bad" in result.output
