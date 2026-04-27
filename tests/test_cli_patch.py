"""CLI tests for the patch apply command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_patch import patch_group
from envctl.patch import PatchResult, PatchError


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config(result: PatchResult | None = None, error: Exception | None = None):
    """Return a context manager that patches Config and patch_profile."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with patch("envctl.cli_patch.Config") as MockCfg, \
             patch("envctl.cli_patch.patch_profile") as mock_patch:
            MockCfg.return_value = MagicMock()
            if error:
                mock_patch.side_effect = error
            else:
                mock_patch.return_value = result or PatchResult(
                    applied={"FOO": "bar"},
                    skipped={},
                    errors=[],
                )
            yield MockCfg, mock_patch

    return _ctx


def test_apply_cmd_success(runner):
    with _mock_config()():
        result = runner.invoke(patch_group, ["apply", "local", "-s", "FOO=bar"])
    assert result.exit_code == 0
    assert "patched  FOO=bar" in result.output
    assert "1 applied" in result.output


def test_apply_cmd_skipped(runner):
    pr = PatchResult(applied={}, skipped={"FOO": "bar"}, errors=[])
    with _mock_config(result=pr)():
        result = runner.invoke(patch_group, ["apply", "local", "-s", "FOO=bar",
                                             "--no-overwrite"])
    assert result.exit_code == 0
    assert "skipped  FOO" in result.output


def test_apply_cmd_dry_run(runner):
    pr = PatchResult(applied={"X": "1"}, skipped={}, errors=[])
    with _mock_config(result=pr)():
        result = runner.invoke(patch_group, ["apply", "prod", "-s", "X=1",
                                             "--dry-run"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output


def test_apply_cmd_error_on_missing_profile(runner):
    with _mock_config(error=PatchError("Profile 'ghost' does not exist."))():
        result = runner.invoke(patch_group, ["apply", "ghost", "-s", "A=1"])
    assert result.exit_code == 1
    assert "Error" in result.output or "Error" in (result.stderr or "")


def test_apply_cmd_bad_pair_format(runner):
    result = runner.invoke(patch_group, ["apply", "local", "-s", "NOEQUALSSIGN"])
    assert result.exit_code != 0
