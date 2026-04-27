"""Tests for envctl.cli_annotate CLI commands."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_annotate import annotate_group
from envctl.annotate import AnnotateError


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config():
    cfg = MagicMock()
    cfg.path = "/fake/config.json"
    return cfg


def test_set_cmd_success(runner):
    with patch("envctl.cli_annotate.Config", return_value=_mock_config()), \
         patch("envctl.cli_annotate.set_annotation") as mock_set:
        result = runner.invoke(annotate_group, ["set", "dev", "API_KEY", "my note"])
    assert result.exit_code == 0
    assert "Annotated" in result.output
    mock_set.assert_called_once()


def test_set_cmd_error(runner):
    with patch("envctl.cli_annotate.Config", return_value=_mock_config()), \
         patch("envctl.cli_annotate.set_annotation", side_effect=AnnotateError("bad")):
        result = runner.invoke(annotate_group, ["set", "dev", "MISSING", "note"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_get_cmd_shows_note(runner):
    with patch("envctl.cli_annotate.Config", return_value=_mock_config()), \
         patch("envctl.cli_annotate.get_annotation", return_value="the note"):
        result = runner.invoke(annotate_group, ["get", "dev", "API_KEY"])
    assert result.exit_code == 0
    assert "the note" in result.output


def test_get_cmd_no_annotation(runner):
    with patch("envctl.cli_annotate.Config", return_value=_mock_config()), \
         patch("envctl.cli_annotate.get_annotation", return_value=None):
        result = runner.invoke(annotate_group, ["get", "dev", "API_KEY"])
    assert result.exit_code == 0
    assert "No annotation" in result.output


def test_remove_cmd_success(runner):
    with patch("envctl.cli_annotate.Config", return_value=_mock_config()), \
         patch("envctl.cli_annotate.remove_annotation", return_value=True):
        result = runner.invoke(annotate_group, ["remove", "dev", "API_KEY"])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_cmd_not_found(runner):
    with patch("envctl.cli_annotate.Config", return_value=_mock_config()), \
         patch("envctl.cli_annotate.remove_annotation", return_value=False):
        result = runner.invoke(annotate_group, ["remove", "dev", "API_KEY"])
    assert result.exit_code == 0
    assert "No annotation found" in result.output


def test_list_cmd_shows_entries(runner):
    with patch("envctl.cli_annotate.Config", return_value=_mock_config()), \
         patch("envctl.cli_annotate.list_annotations", return_value={"A": "note-a", "B": "note-b"}):
        result = runner.invoke(annotate_group, ["list", "dev"])
    assert result.exit_code == 0
    assert "A: note-a" in result.output
    assert "B: note-b" in result.output


def test_list_cmd_empty(runner):
    with patch("envctl.cli_annotate.Config", return_value=_mock_config()), \
         patch("envctl.cli_annotate.list_annotations", return_value={}):
        result = runner.invoke(annotate_group, ["list", "dev"])
    assert result.exit_code == 0
    assert "No annotations" in result.output
