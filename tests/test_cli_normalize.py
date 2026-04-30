"""Tests for envctl.cli_normalize."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_normalize import apply_cmd
from envctl.normalize import NormalizeError, NormalizeResult


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config():
    cfg = MagicMock()
    return cfg


def _invoke(runner, args, cfg=None):
    if cfg is None:
        cfg = _mock_config()
    return runner.invoke(apply_cmd, args, obj={"config": cfg})


# ---------------------------------------------------------------------------

def test_apply_cmd_success(runner):
    result_obj = NormalizeResult(applied={"KEY": "HELLO"}, skipped={"OTHER": "no change"})
    with patch("envctl.cli_normalize.normalize_profile", return_value=result_obj):
        res = _invoke(runner, ["dev", "--strategy", "upper"])
    assert res.exit_code == 0
    assert "normalized" in res.output
    assert "KEY" in res.output


def test_apply_cmd_no_changes(runner):
    result_obj = NormalizeResult()
    with patch("envctl.cli_normalize.normalize_profile", return_value=result_obj):
        res = _invoke(runner, ["dev"])
    assert res.exit_code == 0
    assert "Nothing to normalize" in res.output


def test_apply_cmd_dry_run(runner):
    result_obj = NormalizeResult(applied={"KEY": "hello"})
    with patch("envctl.cli_normalize.normalize_profile", return_value=result_obj) as mock_fn:
        res = _invoke(runner, ["dev", "--strategy", "lower", "--dry-run"])
    assert res.exit_code == 0
    assert "[dry-run]" in res.output
    _, kwargs = mock_fn.call_args
    assert kwargs.get("dry_run") is True


def test_apply_cmd_specific_keys(runner):
    result_obj = NormalizeResult(applied={"A": "a"})
    with patch("envctl.cli_normalize.normalize_profile", return_value=result_obj) as mock_fn:
        res = _invoke(runner, ["dev", "-k", "A", "-k", "B"])
    assert res.exit_code == 0
    _, kwargs = mock_fn.call_args
    assert set(kwargs.get("keys", [])) == {"A", "B"}


def test_apply_cmd_error(runner):
    with patch(
        "envctl.cli_normalize.normalize_profile",
        side_effect=NormalizeError("Profile 'x' not found."),
    ):
        res = _invoke(runner, ["x"])
    assert res.exit_code != 0
    assert "not found" in res.output
