"""CLI tests for the merge apply command."""

from __future__ import annotations

import json
import pathlib
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_merge import apply_cmd
from envctl.merge import MergeResult


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _mock_config(result: MergeResult):
    """Return a context-manager patch that makes merge_profiles return *result*."""
    return patch("envctl.cli_merge.merge_profiles", return_value=result)


def test_apply_cmd_success(runner, tmp_path):
    result = MergeResult(added=["FOO", "BAR"], updated=[], skipped=[], conflicts=[])
    with _mock_config(result):
        out = runner.invoke(apply_cmd, ["staging", "production"])
    assert out.exit_code == 0
    assert "Added (2)" in out.output
    assert "Merged 2 key(s)" in out.output


def test_apply_cmd_conflict_warning(runner):
    result = MergeResult(added=[], updated=[], skipped=[], conflicts=["SECRET"])
    with _mock_config(result):
        out = runner.invoke(apply_cmd, ["staging", "local"])
    assert "Conflicts" in out.output or "Conflicts" in (out.output + str(out.exception))


def test_apply_cmd_nothing_to_merge(runner):
    result = MergeResult(added=[], updated=[], skipped=["FOO"], conflicts=[])
    with _mock_config(result):
        out = runner.invoke(apply_cmd, ["staging", "local"])
    assert out.exit_code == 0
    assert "Nothing to merge" in out.output


def test_apply_cmd_dry_run(runner):
    result = MergeResult(added=["FOO"], updated=[], skipped=[], conflicts=[])
    with _mock_config(result):
        out = runner.invoke(apply_cmd, ["staging", "production", "--dry-run"])
    assert out.exit_code == 0
    assert "[dry-run]" in out.output


def test_apply_cmd_merge_error(runner):
    with patch("envctl.cli_merge.merge_profiles", side_effect=Exception("boom")):
        out = runner.invoke(apply_cmd, ["ghost", "production"])
    assert out.exit_code != 0
