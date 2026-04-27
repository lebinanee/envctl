"""Tests for envctl/cli_protect.py"""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envctl.cli_protect import protect_group
from envctl.protect import protect_key


class FakeConfig:
    def __init__(self, tmp_path):
        self.path = str(tmp_path / "config.json")
        self._profiles = {"local": {"DB_URL": "sqlite", "SECRET": "abc"}}

    def get_profile(self, profile):
        return self._profiles.get(profile)


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def _mock_config(tmp_path):
    return FakeConfig(tmp_path)


def _ctx(cfg):
    return {"config": cfg}


def test_add_cmd_success(runner, _mock_config):
    result = runner.invoke(
        protect_group, ["add", "local", "DB_URL"], obj=_ctx(_mock_config)
    )
    assert result.exit_code == 0
    assert "now protected" in result.output


def test_add_cmd_already_protected(runner, _mock_config):
    protect_key(_mock_config, "local", "DB_URL")
    result = runner.invoke(
        protect_group, ["add", "local", "DB_URL"], obj=_ctx(_mock_config)
    )
    assert result.exit_code == 0
    assert "already protected" in result.output


def test_add_cmd_error_missing_profile(runner, _mock_config):
    result = runner.invoke(
        protect_group, ["add", "ghost", "DB_URL"], obj=_ctx(_mock_config)
    )
    assert result.exit_code != 0 or "Error" in result.output


def test_remove_cmd_success(runner, _mock_config):
    protect_key(_mock_config, "local", "SECRET")
    result = runner.invoke(
        protect_group, ["remove", "local", "SECRET"], obj=_ctx(_mock_config)
    )
    assert result.exit_code == 0
    assert "Protection removed" in result.output


def test_remove_cmd_not_protected(runner, _mock_config):
    result = runner.invoke(
        protect_group, ["remove", "local", "DB_URL"], obj=_ctx(_mock_config)
    )
    assert result.exit_code == 0
    assert "not protected" in result.output


def test_status_cmd_protected(runner, _mock_config):
    protect_key(_mock_config, "local", "DB_URL")
    result = runner.invoke(
        protect_group, ["status", "local", "DB_URL"], obj=_ctx(_mock_config)
    )
    assert "protected" in result.output


def test_list_cmd_empty(runner, _mock_config):
    result = runner.invoke(
        protect_group, ["list", "local"], obj=_ctx(_mock_config)
    )
    assert "No protected keys" in result.output


def test_list_cmd_shows_keys(runner, _mock_config):
    protect_key(_mock_config, "local", "DB_URL")
    protect_key(_mock_config, "local", "SECRET")
    result = runner.invoke(
        protect_group, ["list", "local"], obj=_ctx(_mock_config)
    )
    assert "DB_URL" in result.output
    assert "SECRET" in result.output
