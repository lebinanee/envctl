"""Tests for envctl.cli_prune."""

from __future__ import annotations

from typing import Dict, Optional
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_prune import prune_group
from envctl.prune import PruneError, PruneResult


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _mock_config() -> MagicMock:
    cfg = MagicMock()
    return cfg


def test_apply_cmd_removes_keys(runner):
    result = PruneResult(removed=["EMPTY_KEY"], skipped=["GOOD_KEY"])
    cfg = _mock_config()
    with patch("envctl.cli_prune.prune_profile", return_value=result) as mock_prune:
        outcome = runner.invoke(
            prune_group, ["apply", "dev"], obj=cfg, catch_exceptions=False
        )
    assert outcome.exit_code == 0
    assert "removed: EMPTY_KEY" in outcome.output
    assert "1 removed" in outcome.output


def test_apply_cmd_nothing_to_prune(runner):
    result = PruneResult(removed=[], skipped=["A", "B"])
    cfg = _mock_config()
    with patch("envctl.cli_prune.prune_profile", return_value=result):
        outcome = runner.invoke(
            prune_group, ["apply", "dev"], obj=cfg, catch_exceptions=False
        )
    assert outcome.exit_code == 0
    assert "Nothing to prune" in outcome.output


def test_apply_cmd_dry_run(runner):
    result = PruneResult(removed=["X"], skipped=[])
    cfg = _mock_config()
    with patch("envctl.cli_prune.prune_profile", return_value=result) as mock_prune:
        outcome = runner.invoke(
            prune_group, ["apply", "dev", "--dry-run"], obj=cfg, catch_exceptions=False
        )
    assert outcome.exit_code == 0
    assert "dry-run" in outcome.output
    assert "would remove" in outcome.output
    _, kwargs = mock_prune.call_args
    assert kwargs.get("dry_run") is True


def test_apply_cmd_error(runner):
    cfg = _mock_config()
    with patch(
        "envctl.cli_prune.prune_profile", side_effect=PruneError("Profile not found")
    ):
        outcome = runner.invoke(prune_group, ["apply", "missing"], obj=cfg)
    assert outcome.exit_code != 0
    assert "Profile not found" in outcome.output
