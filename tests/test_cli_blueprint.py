"""CLI tests for blueprint commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envctl.cli_blueprint import blueprint_group


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_config(tmp_path: Path):
    """Return a lightweight fake Config rooted at tmp_path."""
    cfg = MagicMock()
    cfg.path = str(tmp_path / "envctl.json")
    cfg.get_profile.return_value = {}
    return cfg


def test_save_cmd_success(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_blueprint.Config", return_value=cfg), \
         patch("envctl.cli_blueprint.save_blueprint") as mock_save:
        mock_save.return_value = MagicMock(name="base", keys={"HOST": "localhost"})
        mock_save.return_value.name = "base"
        mock_save.return_value.keys = {"HOST": "localhost"}
        result = runner.invoke(blueprint_group, ["save", "base", "HOST=localhost"])
    assert result.exit_code == 0
    assert "saved" in result.output


def test_save_cmd_bad_pair(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_blueprint.Config", return_value=cfg):
        result = runner.invoke(blueprint_group, ["save", "base", "BADPAIR"])
    assert result.exit_code != 0


def test_list_cmd_empty(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_blueprint.Config", return_value=cfg), \
         patch("envctl.cli_blueprint.list_blueprints", return_value=[]):
        result = runner.invoke(blueprint_group, ["list"])
    assert result.exit_code == 0
    assert "No blueprints" in result.output


def test_list_cmd_shows_entries(runner, tmp_path):
    from envctl.blueprint import Blueprint
    cfg = _mock_config(tmp_path)
    bp = Blueprint(name="base", keys={"K": "v"}, description="test")
    with patch("envctl.cli_blueprint.Config", return_value=cfg), \
         patch("envctl.cli_blueprint.list_blueprints", return_value=[bp]):
        result = runner.invoke(blueprint_group, ["list"])
    assert "base" in result.output
    assert "1 keys" in result.output


def test_apply_cmd_success(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_blueprint.Config", return_value=cfg), \
         patch("envctl.cli_blueprint.apply_blueprint", return_value={"HOST": "localhost"}):
        result = runner.invoke(blueprint_group, ["apply", "base", "local"])
    assert result.exit_code == 0
    assert "Applied 1" in result.output


def test_apply_cmd_nothing_to_apply(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_blueprint.Config", return_value=cfg), \
         patch("envctl.cli_blueprint.apply_blueprint", return_value={}):
        result = runner.invoke(blueprint_group, ["apply", "base", "local"])
    assert "Nothing to apply" in result.output


def test_delete_cmd_success(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_blueprint.Config", return_value=cfg), \
         patch("envctl.cli_blueprint.delete_blueprint", return_value=True):
        result = runner.invoke(blueprint_group, ["delete", "base"])
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_delete_cmd_not_found(runner, tmp_path):
    cfg = _mock_config(tmp_path)
    with patch("envctl.cli_blueprint.Config", return_value=cfg), \
         patch("envctl.cli_blueprint.delete_blueprint", return_value=False):
        result = runner.invoke(blueprint_group, ["delete", "ghost"])
    assert result.exit_code != 0
