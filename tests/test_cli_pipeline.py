"""Tests for envctl.cli_pipeline."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_pipeline import pipeline_group
from envctl.pipeline import PipelineError, PipelineResult


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config(profile_vars: dict | None = None):
    cfg = MagicMock()
    cfg.get_profile.return_value = profile_vars or {"FOO": "hello"}
    return cfg


def test_run_cmd_success(runner):
    result_obj = PipelineResult(
        profile="local",
        steps_applied=["uppercase-values"],
        final_vars={"FOO": "HELLO"},
    )
    with patch("envctl.cli_pipeline.Config") as MockCfg, \
         patch("envctl.cli_pipeline.run_pipeline", return_value=result_obj), \
         patch("envctl.cli_pipeline.build_pipeline", side_effect=lambda s: s):
        MockCfg.return_value = _mock_config()
        result = runner.invoke(
            pipeline_group,
            ["run", "local", "--step", "uppercase-values"],
        )
    assert result.exit_code == 0
    assert "[ok] uppercase-values" in result.output
    assert "1 step(s) applied" in result.output


def test_run_cmd_dry_run(runner):
    result_obj = PipelineResult(
        profile="local",
        steps_applied=["strip-whitespace"],
        final_vars={"FOO": "hello"},
    )
    with patch("envctl.cli_pipeline.Config") as MockCfg, \
         patch("envctl.cli_pipeline.run_pipeline", return_value=result_obj), \
         patch("envctl.cli_pipeline.build_pipeline", side_effect=lambda s: s):
        MockCfg.return_value = _mock_config()
        result = runner.invoke(
            pipeline_group,
            ["run", "local", "--step", "strip-whitespace", "--dry-run"],
        )
    assert result.exit_code == 0
    assert "Dry run" in result.output


def test_run_cmd_unknown_step(runner):
    with patch("envctl.cli_pipeline.Config") as MockCfg:
        MockCfg.return_value = _mock_config()
        result = runner.invoke(
            pipeline_group,
            ["run", "local", "--step", "nonexistent-step"],
        )
    assert result.exit_code != 0
    assert "Unknown step" in result.output


def test_run_cmd_pipeline_error(runner):
    with patch("envctl.cli_pipeline.Config") as MockCfg, \
         patch("envctl.cli_pipeline.build_pipeline", side_effect=lambda s: s), \
         patch("envctl.cli_pipeline.run_pipeline", side_effect=PipelineError("bad profile")):
        MockCfg.return_value = _mock_config()
        result = runner.invoke(
            pipeline_group,
            ["run", "missing", "--step", "strip-whitespace"],
        )
    assert result.exit_code != 0
    assert "Pipeline error" in result.output
