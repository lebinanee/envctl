"""Tests for envctl.namespace."""
from __future__ import annotations

import pytest

from envctl.namespace import (
    NamespaceError,
    delete_namespace,
    get_namespace,
    list_namespaces,
    rename_namespace,
    set_namespace,
)


def _profile() -> dict:
    return {
        "DB__HOST": "localhost",
        "DB__PORT": "5432",
        "CACHE__HOST": "redis",
        "PLAIN_KEY": "value",
    }


def test_list_namespaces_returns_sorted():
    ns = list_namespaces(_profile())
    assert ns == ["CACHE", "DB"]


def test_list_namespaces_empty_when_no_separator():
    assert list_namespaces({"FOO": "bar", "BAZ": "qux"}) == []


def test_get_namespace_returns_matching_keys():
    pairs = get_namespace(_profile(), "DB")
    assert pairs == {"DB__HOST": "localhost", "DB__PORT": "5432"}


def test_get_namespace_case_insensitive_input():
    pairs = get_namespace(_profile(), "db")
    assert "DB__HOST" in pairs


def test_get_namespace_returns_empty_for_unknown():
    assert get_namespace(_profile(), "UNKNOWN") == {}


def test_set_namespace_adds_keys():
    profile: dict = {}
    result = set_namespace(profile, "APP", {"NAME": "envctl", "VERSION": "1"})
    assert result["added"] == 2
    assert result["skipped"] == 0
    assert profile["APP__NAME"] == "envctl"
    assert profile["APP__VERSION"] == "1"


def test_set_namespace_skips_existing_without_overwrite():
    profile = {"APP__NAME": "old"}
    result = set_namespace(profile, "APP", {"NAME": "new"}, overwrite=False)
    assert result["skipped"] == 1
    assert profile["APP__NAME"] == "old"


def test_set_namespace_overwrites_when_flag_set():
    profile = {"APP__NAME": "old"}
    result = set_namespace(profile, "APP", {"NAME": "new"}, overwrite=True)
    assert result["added"] == 1
    assert profile["APP__NAME"] == "new"


def test_set_namespace_invalid_name_raises():
    with pytest.raises(NamespaceError):
        set_namespace({}, "123bad", {"K": "v"})


def test_delete_namespace_removes_keys():
    profile = _profile()
    count = delete_namespace(profile, "DB")
    assert count == 2
    assert "DB__HOST" not in profile
    assert "DB__PORT" not in profile
    assert "CACHE__HOST" in profile


def test_delete_namespace_returns_zero_for_unknown():
    profile = _profile()
    assert delete_namespace(profile, "GHOST") == 0


def test_rename_namespace_updates_keys():
    profile = _profile()
    count = rename_namespace(profile, "DB", "DATABASE")
    assert count == 2
    assert "DATABASE__HOST" in profile
    assert "DATABASE__PORT" in profile
    assert "DB__HOST" not in profile


def test_rename_namespace_invalid_new_name_raises():
    with pytest.raises(NamespaceError):
        rename_namespace(_profile(), "DB", "99bad")


def test_rename_namespace_unknown_old_returns_zero():
    profile = _profile()
    count = rename_namespace(profile, "GHOST", "SPIRIT")
    assert count == 0
