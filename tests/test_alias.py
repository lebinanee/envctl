"""Tests for envctl.alias."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envctl.alias import (
    AliasError,
    list_aliases,
    remove_alias,
    resolve_alias,
    resolve_key,
    set_alias,
)


class _FakeConfig:
    def __init__(self, tmp_path: Path):
        self.path = str(tmp_path / "envctl.json")


@pytest.fixture()
def cfg(tmp_path):
    return _FakeConfig(tmp_path)


def test_set_alias_creates_file(cfg, tmp_path):
    set_alias(cfg, "db", "DATABASE_URL")
    alias_file = tmp_path / ".envctl_aliases.json"
    assert alias_file.exists()
    data = json.loads(alias_file.read_text())
    assert data["db"] == "DATABASE_URL"


def test_set_alias_overwrites_existing(cfg):
    set_alias(cfg, "db", "DATABASE_URL")
    set_alias(cfg, "db", "DB_URL")
    assert resolve_alias(cfg, "db") == "DB_URL"


def test_set_alias_invalid_name_raises(cfg):
    with pytest.raises(AliasError, match="Invalid alias"):
        set_alias(cfg, "bad name", "SOME_KEY")


def test_set_alias_empty_name_raises(cfg):
    with pytest.raises(AliasError):
        set_alias(cfg, "", "SOME_KEY")


def test_set_alias_empty_key_raises(cfg):
    with pytest.raises(AliasError, match="Key must not be empty"):
        set_alias(cfg, "myalias", "")


def test_resolve_alias_returns_key(cfg):
    set_alias(cfg, "token", "API_TOKEN")
    assert resolve_alias(cfg, "token") == "API_TOKEN"


def test_resolve_alias_missing_returns_none(cfg):
    assert resolve_alias(cfg, "nonexistent") is None


def test_remove_alias_returns_true(cfg):
    set_alias(cfg, "host", "DB_HOST")
    result = remove_alias(cfg, "host")
    assert result is True
    assert resolve_alias(cfg, "host") is None


def test_remove_alias_missing_returns_false(cfg):
    assert remove_alias(cfg, "ghost") is False


def test_list_aliases_empty(cfg):
    assert list_aliases(cfg) == {}


def test_list_aliases_multiple(cfg):
    set_alias(cfg, "db", "DATABASE_URL")
    set_alias(cfg, "secret", "SECRET_KEY")
    aliases = list_aliases(cfg)
    assert aliases == {"db": "DATABASE_URL", "secret": "SECRET_KEY"}


def test_resolve_key_with_alias(cfg):
    set_alias(cfg, "pw", "DB_PASSWORD")
    assert resolve_key(cfg, "pw") == "DB_PASSWORD"


def test_resolve_key_without_alias_returns_name(cfg):
    assert resolve_key(cfg, "PLAIN_KEY") == "PLAIN_KEY"
