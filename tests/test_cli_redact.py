"""CLI tests for the redact show command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_redact import show_cmd
from envctl.redact import PLACEHOLDER, RedactResult


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config(profiles: dict):
    cfg = MagicMock()
    cfg.get_profile.side_effect = lambda name: profiles.get(name)
    return cfg


def test_show_cmd_redacts_sensitive(runner):
    result_obj = RedactResult(
        redacted={"DB_PASSWORD": PLACEHOLDER, "APP_NAME": "envctl"},
        redacted_keys=["DB_PASSWORD"],
        skipped_keys=["APP_NAME"],
    )
    with patch("envctl.cli_redact.Config"), patch(
        "envctl.cli_redact.redact_profile", return_value=result_obj
    ):
        result = runner.invoke(show_cmd, ["prod"])

    assert result.exit_code == 0
    assert PLACEHOLDER in result.output
    assert "1 key(s) redacted" in result.output
    assert "DB_PASSWORD" in result.output


def test_show_cmd_empty_profile(runner):
    result_obj = RedactResult(redacted={}, redacted_keys=[], skipped_keys=[])
    with patch("envctl.cli_redact.Config"), patch(
        "envctl.cli_redact.redact_profile", return_value=result_obj
    ):
        result = runner.invoke(show_cmd, ["empty"])

    assert result.exit_code == 0
    assert "empty" in result.output


def test_show_cmd_error_on_missing_profile(runner):
    from envctl.redact import RedactError

    with patch("envctl.cli_redact.Config"), patch(
        "envctl.cli_redact.redact_profile", side_effect=RedactError("Profile 'x' not found.")
    ):
        result = runner.invoke(show_cmd, ["x"])

    assert result.exit_code != 0
    assert "not found" in result.output


def test_show_cmd_explicit_key_flag(runner):
    result_obj = RedactResult(
        redacted={"REGION": PLACEHOLDER},
        redacted_keys=["REGION"],
        skipped_keys=[],
    )
    with patch("envctl.cli_redact.Config"), patch(
        "envctl.cli_redact.redact_profile", return_value=result_obj
    ) as mock_redact:
        result = runner.invoke(show_cmd, ["dev", "-k", "REGION", "--no-auto"])

    assert result.exit_code == 0
    mock_redact.assert_called_once()
    _, kwargs = mock_redact.call_args
    assert "REGION" in kwargs.get("keys", [])
    assert kwargs.get("auto") is False
