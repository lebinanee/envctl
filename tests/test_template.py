"""Tests for envctl.template."""

from __future__ import annotations

import json
import pytest

from envctl.config import Config
from envctl.template import TemplateError, render_template


@pytest.fixture()
def make_config(tmp_path):
    def _make(profiles: dict) -> Config:
        data = {"active_env": "local", "profiles": profiles}
        p = tmp_path / "envctl.json"
        p.write_text(json.dumps(data))
        return Config(str(p))

    return _make


def test_render_simple(make_config):
    cfg = make_config({"local": {"NAME": "world"}})
    result = render_template("Hello, {{NAME}}!", cfg)
    assert result.output == "Hello, world!"
    assert "NAME" in result.resolved
    assert result.missing == []


def test_render_multiple_keys(make_config):
    cfg = make_config({"local": {"HOST": "localhost", "PORT": "5432"}})
    result = render_template("{{HOST}}:{{PORT}}", cfg)
    assert result.output == "localhost:5432"
    assert set(result.resolved) == {"HOST", "PORT"}


def test_render_missing_key_non_strict(make_config):
    cfg = make_config({"local": {}})
    result = render_template("Hello, {{NAME}}!", cfg)
    assert result.output == "Hello, {{NAME}}!"
    assert "NAME" in result.missing


def test_render_missing_key_strict_raises(make_config):
    cfg = make_config({"local": {}})
    with pytest.raises(TemplateError, match="NAME"):
        render_template("Hello, {{NAME}}!", cfg, strict=True)


def test_render_explicit_profile(make_config):
    cfg = make_config(
        {"local": {"ENV": "local"}, "production": {"ENV": "prod"}}
    )
    result = render_template("env={{ENV}}", cfg, profile="production")
    assert result.output == "env=prod"


def test_render_whitespace_in_placeholder(make_config):
    cfg = make_config({"local": {"KEY": "value"}})
    result = render_template("{{ KEY }}", cfg)
    assert result.output == "value"


def test_render_no_placeholders(make_config):
    cfg = make_config({"local": {"KEY": "value"}})
    result = render_template("plain text", cfg)
    assert result.output == "plain text"
    assert result.resolved == []
    assert result.missing == []
