"""Tests for envctl.cli_trim."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_trim import trim_group
from envctl.trim import TrimError, TrimResult


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config():
    cfg = MagicMock()
    return cfg


def _invoke(runner, args, config=None):
    cfg = config or _mock_config()
    return runner.invoke(trim_group, args, obj={"config": cfg})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_apply_cmd_trims_values(runner):
    result_obj = TrimResult(trimmed=["FOO"], skipped=["BAR"])
    with patch("envctl.cli_trim.trim_profile", return_value=result_obj):
        res = _invoke(runner, ["apply", "dev"])
    assert res.exit_code == 0
    assert "trimmed: FOO" in res.output
    assert "1 trimmed" in res.output


def test_apply_cmd_no_changes(runner):
    result_obj = TrimResult(trimmed=[], skipped=["FOO"])
    with patch("envctl.cli_trim.trim_profile", return_value=result_obj):
        res = _invoke(runner, ["apply", "dev"])
    assert res.exit_code == 0
    assert "No values required trimming" in res.output


def test_apply_cmd_dry_run(runner):
    result_obj = TrimResult(trimmed=["FOO"], skipped=[])
    with patch("envctl.cli_trim.trim_profile", return_value=result_obj) as mock_fn:
        res = _invoke(runner, ["apply", "dev", "--dry-run"])
    assert res.exit_code == 0
    assert "dry-run" in res.output
    _, kwargs = mock_fn.call_args
    assert kwargs.get("dry_run") is True


def test_apply_cmd_with_keys(runner):
    result_obj = TrimResult(trimmed=["FOO"], skipped=[])
    with patch("envctl.cli_trim.trim_profile", return_value=result_obj) as mock_fn:
        res = _invoke(runner, ["apply", "dev", "--key", "FOO", "--key", "BAR"])
    assert res.exit_code == 0
    _, kwargs = mock_fn.call_args
    assert "FOO" in kwargs.get("keys", [])
    assert "BAR" in kwargs.get("keys", [])


def test_apply_cmd_error(runner):
    with patch("envctl.cli_trim.trim_profile", side_effect=TrimError("Profile 'x' does not exist.")):
        res = _invoke(runner, ["apply", "x"])
    assert res.exit_code != 0
    assert "does not exist" in res.output
