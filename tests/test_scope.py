"""Tests for envctl.scope."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envctl.scope import (
    ScopeError,
    apply_scope,
    get_scope,
    list_scopes,
    set_scope,
)


@pytest.fixture()
def scope_dir(tmp_path: Path) -> str:
    return str(tmp_path)


# ---------------------------------------------------------------------------
# set_scope / get_scope
# ---------------------------------------------------------------------------

def test_set_scope_creates_file(scope_dir):
    set_scope(scope_dir, "staging", ["DB_URL", "API_KEY"])
    scope_file = Path(scope_dir) / ".envctl_scopes.json"
    assert scope_file.exists()


def test_set_scope_persists_keys(scope_dir):
    set_scope(scope_dir, "staging", ["DB_URL", "API_KEY"])
    scope = get_scope(scope_dir, "staging")
    assert scope == ["API_KEY", "DB_URL"]  # sorted


def test_get_scope_returns_none_when_undefined(scope_dir):
    assert get_scope(scope_dir, "production") is None


def test_set_scope_empty_list_removes_profile(scope_dir):
    set_scope(scope_dir, "staging", ["DB_URL"])
    set_scope(scope_dir, "staging", [])
    assert get_scope(scope_dir, "staging") is None


def test_set_scope_deduplicates_keys(scope_dir):
    set_scope(scope_dir, "local", ["KEY", "KEY", "OTHER"])
    scope = get_scope(scope_dir, "local")
    assert scope == ["KEY", "OTHER"]


def test_set_scope_empty_profile_raises(scope_dir):
    with pytest.raises(ScopeError):
        set_scope(scope_dir, "", ["KEY"])


# ---------------------------------------------------------------------------
# list_scopes
# ---------------------------------------------------------------------------

def test_list_scopes_empty(scope_dir):
    assert list_scopes(scope_dir) == {}


def test_list_scopes_multiple_profiles(scope_dir):
    set_scope(scope_dir, "local", ["A"])
    set_scope(scope_dir, "staging", ["B", "C"])
    scopes = list_scopes(scope_dir)
    assert set(scopes.keys()) == {"local", "staging"}


# ---------------------------------------------------------------------------
# apply_scope
# ---------------------------------------------------------------------------

def test_apply_scope_none_returns_all():
    vars_ = {"A": "1", "B": "2"}
    assert apply_scope(vars_, None) == {"A": "1", "B": "2"}


def test_apply_scope_filters_keys():
    vars_ = {"A": "1", "B": "2", "C": "3"}
    result = apply_scope(vars_, ["A", "C"])
    assert result == {"A": "1", "C": "3"}


def test_apply_scope_empty_scope_returns_empty():
    vars_ = {"A": "1", "B": "2"}
    assert apply_scope(vars_, []) == {}


def test_apply_scope_scope_with_missing_key():
    vars_ = {"A": "1"}
    result = apply_scope(vars_, ["A", "MISSING"])
    assert result == {"A": "1"}
