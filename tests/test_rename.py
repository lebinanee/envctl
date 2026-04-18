"""Tests for envctl.rename."""

from __future__ import annotations
import json
import pytest
from click.testing import CliRunner
from envctl.config import Config
from envctl.rename import rename_key, RenameError
from envctl.validate import ValidationError
from envctl.cli_rename import rename_group


@pytest.fixture()
def make_config(tmp_path):
    def _make(profiles: dict) -> Config:
        path = tmp_path / "envctl.json"
        path.write_text(json.dumps({"active": "local", "profiles": profiles}))
        return Config(str(path))
    return _make


def test_rename_single_profile(make_config):
    cfg = make_config({"local": {"OLD": "val"}})
    results = rename_key(cfg, "OLD", "NEW", profile="local")
    assert results == {"local": True}
    assert cfg.data["profiles"]["local"]["NEW"] == "val"
    assert "OLD" not in cfg.data["profiles"]["local"]


def test_rename_all_profiles(make_config):
    cfg = make_config({"local": {"KEY": "a"}, "prod": {"KEY": "b"}})
    results = rename_key(cfg, "KEY", "NEW_KEY")
    assert results == {"local": True, "prod": True}


def test_rename_missing_key_returns_false(make_config):
    cfg = make_config({"local": {"OTHER": "x"}})
    results = rename_key(cfg, "MISSING", "NEW", profile="local")
    assert results == {"local": False}


def test_rename_conflict_raises(make_config):
    cfg = make_config({"local": {"OLD": "1", "NEW": "2"}})
    with pytest.raises(RenameError, match="already exists"):
        rename_key(cfg, "OLD", "NEW", profile="local")


def test_rename_invalid_key_raises(make_config):
    cfg = make_config({"local": {"VALID": "v"}})
    with pytest.raises(ValidationError):
        rename_key(cfg, "invalid", "NEW", profile="local")


# CLI tests

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_rename_success(runner, make_config, monkeypatch):
    cfg = make_config({"local": {"OLD": "v"}})
    monkeypatch.setattr("envctl.cli_rename.Config", lambda _path: cfg)
    result = runner.invoke(rename_group, ["key", "OLD", "NEW"])
    assert result.exit_code == 0
    assert "OLD" in result.output
    assert "NEW" in result.output


def test_cli_rename_not_found(runner, make_config, monkeypatch):
    cfg = make_config({"local": {}})
    monkeypatch.setattr("envctl.cli_rename.Config", lambda _path: cfg)
    result = runner.invoke(rename_group, ["key", "GHOST", "NEW"])
    assert result.exit_code != 0
    assert "not found" in result.output
