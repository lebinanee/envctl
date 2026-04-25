"""Tests for envctl.group."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envctl.group import (
    GroupError,
    add_to_group,
    remove_from_group,
    get_group,
    list_groups,
    delete_group,
    keys_for_groups,
)


@pytest.fixture()
def make_config(tmp_path):
    def _make():
        cfg = MagicMock()
        cfg.path = str(tmp_path / "envctl.json")
        return cfg
    return _make


def test_add_to_group_new_key(make_config):
    cfg = make_config()
    result = add_to_group(cfg, "backend", "DB_URL")
    assert result is True
    assert "DB_URL" in get_group(cfg, "backend")


def test_add_to_group_duplicate_returns_false(make_config):
    cfg = make_config()
    add_to_group(cfg, "backend", "DB_URL")
    result = add_to_group(cfg, "backend", "DB_URL")
    assert result is False
    assert get_group(cfg, "backend").count("DB_URL") == 1


def test_remove_from_group_success(make_config):
    cfg = make_config()
    add_to_group(cfg, "backend", "DB_URL")
    result = remove_from_group(cfg, "backend", "DB_URL")
    assert result is True
    assert get_group(cfg, "backend") == []


def test_remove_from_group_not_found(make_config):
    cfg = make_config()
    result = remove_from_group(cfg, "backend", "MISSING_KEY")
    assert result is False


def test_remove_last_member_deletes_group(make_config):
    cfg = make_config()
    add_to_group(cfg, "backend", "DB_URL")
    remove_from_group(cfg, "backend", "DB_URL")
    assert "backend" not in list_groups(cfg)


def test_list_groups_returns_all(make_config):
    cfg = make_config()
    add_to_group(cfg, "backend", "DB_URL")
    add_to_group(cfg, "backend", "DB_PASS")
    add_to_group(cfg, "frontend", "API_KEY")
    groups = list_groups(cfg)
    assert set(groups.keys()) == {"backend", "frontend"}
    assert set(groups["backend"]) == {"DB_URL", "DB_PASS"}


def test_delete_group_success(make_config):
    cfg = make_config()
    add_to_group(cfg, "ops", "SENTRY_DSN")
    result = delete_group(cfg, "ops")
    assert result is True
    assert list_groups(cfg) == {}


def test_delete_group_missing_returns_false(make_config):
    cfg = make_config()
    assert delete_group(cfg, "nonexistent") is False


def test_keys_for_groups_deduplicates(make_config):
    cfg = make_config()
    add_to_group(cfg, "a", "SHARED")
    add_to_group(cfg, "a", "ONLY_A")
    add_to_group(cfg, "b", "SHARED")
    add_to_group(cfg, "b", "ONLY_B")
    keys = keys_for_groups(cfg, ["a", "b"])
    assert keys.count("SHARED") == 1
    assert set(keys) == {"SHARED", "ONLY_A", "ONLY_B"}


def test_get_group_missing_returns_empty(make_config):
    cfg = make_config()
    assert get_group(cfg, "ghost") == []
