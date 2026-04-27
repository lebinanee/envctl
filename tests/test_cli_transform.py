"""CLI tests for the transform command group."""
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_transform import apply_cmd
from envctl.transform import TransformError, TransformResult


@pytest.fixture
def runner():
    return CliRunner()


def _mock_config(result):
    cfg = MagicMock()
    with patch("envctl.cli_transform.Config", return_value=cfg), \
         patch("envctl.cli_transform.transform_profile", return_value=result) as mock_fn:
        yield cfg, mock_fn


def test_apply_cmd_success(runner):
    result = TransformResult(applied={"KEY": "VALUE"}, skipped=[])
    with patch("envctl.cli_transform.Config"), \
         patch("envctl.cli_transform.transform_profile", return_value=result):
        out = runner.invoke(apply_cmd, ["dev", "upper"])
    assert out.exit_code == 0
    assert "KEY -> VALUE" in out.output
    assert "Applied 'upper' to 1 key(s)" in out.output


def test_apply_cmd_no_changes(runner):
    result = TransformResult(applied={}, skipped=["KEY"])
    with patch("envctl.cli_transform.Config"), \
         patch("envctl.cli_transform.transform_profile", return_value=result):
        out = runner.invoke(apply_cmd, ["dev", "upper"])
    assert out.exit_code == 0
    assert "No changes" in out.output


def test_apply_cmd_dry_run(runner):
    result = TransformResult(applied={"DB_URL": "POSTGRES://..."}, skipped=[])
    with patch("envctl.cli_transform.Config"), \
         patch("envctl.cli_transform.transform_profile", return_value=result):
        out = runner.invoke(apply_cmd, ["dev", "upper", "--dry-run"])
    assert out.exit_code == 0
    assert "[dry-run]" in out.output
    assert "would be updated" in out.output


def test_apply_cmd_error(runner):
    with patch("envctl.cli_transform.Config"), \
         patch(
             "envctl.cli_transform.transform_profile",
             side_effect=TransformError("Unknown transform 'bad'"),
         ):
        out = runner.invoke(apply_cmd, ["dev", "bad"])
    assert out.exit_code != 0
    assert "Unknown transform" in out.output


def test_apply_cmd_with_keys(runner):
    result = TransformResult(applied={"A": "a"}, skipped=["B"])
    with patch("envctl.cli_transform.Config"), \
         patch("envctl.cli_transform.transform_profile", return_value=result) as mock_fn:
        out = runner.invoke(apply_cmd, ["dev", "lower", "--key", "A"])
    assert out.exit_code == 0
    assert "Skipped 1 unchanged" in out.output
