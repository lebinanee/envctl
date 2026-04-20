"""Tests for envctl.schema."""
import pytest

from envctl.config import Config
from envctl.schema import (
    SchemaField,
    SchemaViolation,
    add_field,
    get_schema,
    remove_field,
    validate_against_schema,
)


@pytest.fixture()
def make_config(tmp_path):
    def _make(profiles=None):
        cfg = Config(config_path=tmp_path / "envctl.json")
        if profiles:
            for name, vars_ in profiles.items():
                cfg._data.setdefault("profiles", {})[name] = vars_
            cfg.save()
        return cfg
    return _make


def test_get_schema_empty(make_config):
    cfg = make_config()
    assert get_schema(cfg) == []


def test_add_field_persists(make_config):
    cfg = make_config()
    f = SchemaField(key="DB_URL", required=True, description="Database URL")
    add_field(cfg, f)
    fields = get_schema(cfg)
    assert len(fields) == 1
    assert fields[0].key == "DB_URL"
    assert fields[0].required is True
    assert fields[0].description == "Database URL"


def test_add_field_replaces_existing(make_config):
    cfg = make_config()
    add_field(cfg, SchemaField(key="API_KEY", required=True))
    add_field(cfg, SchemaField(key="API_KEY", required=False, default="none"))
    fields = get_schema(cfg)
    assert len(fields) == 1
    assert fields[0].required is False
    assert fields[0].default == "none"


def test_remove_field_returns_true(make_config):
    cfg = make_config()
    add_field(cfg, SchemaField(key="TOKEN"))
    assert remove_field(cfg, "TOKEN") is True
    assert get_schema(cfg) == []


def test_remove_field_missing_returns_false(make_config):
    cfg = make_config()
    assert remove_field(cfg, "GHOST") is False


def test_validate_no_schema_passes(make_config):
    cfg = make_config(profiles={"local": {"FOO": "bar"}})
    violations = validate_against_schema(cfg, "local")
    assert violations == []


def test_validate_all_required_keys_present(make_config):
    cfg = make_config(profiles={"local": {"DB_URL": "postgres://localhost"}})
    add_field(cfg, SchemaField(key="DB_URL", required=True))
    assert validate_against_schema(cfg, "local") == []


def test_validate_missing_required_key(make_config):
    cfg = make_config(profiles={"local": {}})
    add_field(cfg, SchemaField(key="SECRET_KEY", required=True))
    violations = validate_against_schema(cfg, "local")
    assert len(violations) == 1
    assert violations[0].key == "SECRET_KEY"
    assert "missing" in violations[0].message


def test_validate_optional_key_missing_no_violation(make_config):
    cfg = make_config(profiles={"local": {}})
    add_field(cfg, SchemaField(key="LOG_LEVEL", required=False, default="INFO"))
    assert validate_against_schema(cfg, "local") == []


def test_schema_violation_str():
    v = SchemaViolation(key="API_KEY", message="required key is missing")
    assert str(v) == "API_KEY: required key is missing"
