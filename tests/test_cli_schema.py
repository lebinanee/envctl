"""Tests for envctl.cli_schema CLI commands."""
import json
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from envctl.cli_schema import schema_group
from envctl.schema import SchemaField, add_field


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def _mock_config(tmp_path):
    from envctl.config import Config

    def _make(profiles=None):
        cfg = Config(config_path=tmp_path / "envctl.json")
        if profiles:
            for name, vars_ in profiles.items():
                cfg._data.setdefault("profiles", {})[name] = vars_
            cfg.save()
        return {"config": cfg}

    return _make


def test_add_cmd_success(runner, _mock_config):
    obj = _mock_config()
    result = runner.invoke(schema_group, ["add", "DB_URL", "--description", "db conn"], obj=obj)
    assert result.exit_code == 0
    assert "DB_URL" in result.output


def test_add_cmd_optional(runner, _mock_config):
    obj = _mock_config()
    result = runner.invoke(schema_group, ["add", "LOG_LEVEL", "--optional", "--default", "INFO"], obj=obj)
    assert result.exit_code == 0
    from envctl.schema import get_schema
    fields = get_schema(obj["config"])
    assert fields[0].required is False
    assert fields[0].default == "INFO"


def test_list_cmd_empty(runner, _mock_config):
    obj = _mock_config()
    result = runner.invoke(schema_group, ["list"], obj=obj)
    assert result.exit_code == 0
    assert "No schema fields" in result.output


def test_list_cmd_shows_fields(runner, _mock_config):
    obj = _mock_config()
    add_field(obj["config"], SchemaField(key="API_KEY", required=True, description="The API key"))
    result = runner.invoke(schema_group, ["list"], obj=obj)
    assert "API_KEY" in result.output
    assert "required" in result.output
    assert "The API key" in result.output


def test_remove_cmd_success(runner, _mock_config):
    obj = _mock_config()
    add_field(obj["config"], SchemaField(key="TOKEN"))
    result = runner.invoke(schema_group, ["remove", "TOKEN"], obj=obj)
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_cmd_missing_exits_1(runner, _mock_config):
    obj = _mock_config()
    result = runner.invoke(schema_group, ["remove", "GHOST"], obj=obj)
    assert result.exit_code == 1


def test_validate_cmd_valid_profile(runner, _mock_config):
    obj = _mock_config(profiles={"staging": {"DB_URL": "postgres://staging"}})
    add_field(obj["config"], SchemaField(key="DB_URL", required=True))
    result = runner.invoke(schema_group, ["validate", "staging"], obj=obj)
    assert result.exit_code == 0
    assert "valid" in result.output


def test_validate_cmd_invalid_profile(runner, _mock_config):
    obj = _mock_config(profiles={"prod": {}})
    add_field(obj["config"], SchemaField(key="SECRET_KEY", required=True))
    result = runner.invoke(schema_group, ["validate", "prod"], obj=obj)
    assert result.exit_code == 1
