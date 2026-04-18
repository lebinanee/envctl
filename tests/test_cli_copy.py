"""Tests for envctl.cli_copy module."""
import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envctl.cli_copy import copy_group
from envctl.copy import CopyError


@pytest.fixture
def runner():
    return CliRunner()


def _mock_config(result):
    mock = MagicMock()
    return mock, result


def test_copy_cmd_success(runner):
    with patch("envctl.cli_copy.Config") as MockCfg, \
         patch("envctl.cli_copy.copy_keys") as mock_copy:
        mock_copy.return_value = {"copied": ["PORT"], "skipped": []}
        res = runner.invoke(copy_group, ["run", "local", "staging", "-k", "PORT"])
        assert res.exit_code == 0
        assert "Copied: PORT" in res.output


def test_copy_cmd_skipped(runner):
    with patch("envctl.cli_copy.Config"), \
         patch("envctl.cli_copy.copy_keys") as mock_copy:
        mock_copy.return_value = {"copied": [], "skipped": ["DB"]}
        res = runner.invoke(copy_group, ["run", "local", "staging"])
        assert res.exit_code == 0
        assert "Skipped" in res.output


def test_copy_cmd_error(runner):
    with patch("envctl.cli_copy.Config"), \
         patch("envctl.cli_copy.copy_keys", side_effect=CopyError("bad")):
        res = runner.invoke(copy_group, ["run", "local", "staging"])
        assert res.exit_code == 1
        assert "Error: bad" in res.output


def test_copy_cmd_nothing(runner):
    with patch("envctl.cli_copy.Config"), \
         patch("envctl.cli_copy.copy_keys") as mock_copy:
        mock_copy.return_value = {"copied": [], "skipped": []}
        res = runner.invoke(copy_group, ["run", "local", "staging"])
        assert "Nothing to copy" in res.output
