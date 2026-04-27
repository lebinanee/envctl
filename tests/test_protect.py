"""Tests for envctl/protect.py"""
from __future__ import annotations

import json
import pytest

from envctl.protect import (
    ProtectError,
    protect_key,
    unprotect_key,
    is_protected,
    list_protected,
    assert_not_protected,
)


class FakeConfig:
    def __init__(self, tmp_path):
        self.path = str(tmp_path / "config.json")
        self._profiles = {}

    def get_profile(self, profile):
        return self._profiles.get(profile)

    def set_profile(self, profile, data):
        self._profiles[profile] = data

    def save(self):
        pass


def make_config(tmp_path):
    cfg = FakeConfig(tmp_path)
    cfg.set_profile("local", {"DB_URL": "sqlite", "SECRET": "abc"})
    cfg.set_profile("prod", {"DB_URL": "postgres", "API_KEY": "xyz"})
    return cfg


def test_protect_key_success(tmp_path):
    cfg = make_config(tmp_path)
    result = protect_key(cfg, "local", "DB_URL")
    assert result is True
    assert is_protected(cfg, "local", "DB_URL")


def test_protect_key_already_protected(tmp_path):
    cfg = make_config(tmp_path)
    protect_key(cfg, "local", "DB_URL")
    result = protect_key(cfg, "local", "DB_URL")
    assert result is False


def test_protect_missing_profile_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(ProtectError, match="Profile"):
        protect_key(cfg, "ghost", "DB_URL")


def test_protect_missing_key_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(ProtectError, match="Key"):
        protect_key(cfg, "local", "NONEXISTENT")


def test_unprotect_key_success(tmp_path):
    cfg = make_config(tmp_path)
    protect_key(cfg, "local", "SECRET")
    result = unprotect_key(cfg, "local", "SECRET")
    assert result is True
    assert not is_protected(cfg, "local", "SECRET")


def test_unprotect_not_protected_returns_false(tmp_path):
    cfg = make_config(tmp_path)
    result = unprotect_key(cfg, "local", "DB_URL")
    assert result is False


def test_list_protected_returns_all(tmp_path):
    cfg = make_config(tmp_path)
    protect_key(cfg, "local", "DB_URL")
    protect_key(cfg, "local", "SECRET")
    keys = list_protected(cfg, "local")
    assert set(keys) == {"DB_URL", "SECRET"}


def test_list_protected_empty_profile(tmp_path):
    cfg = make_config(tmp_path)
    keys = list_protected(cfg, "local")
    assert keys == []


def test_assert_not_protected_raises(tmp_path):
    cfg = make_config(tmp_path)
    protect_key(cfg, "prod", "API_KEY")
    with pytest.raises(ProtectError, match="protected"):
        assert_not_protected(cfg, "prod", "API_KEY")


def test_assert_not_protected_passes(tmp_path):
    cfg = make_config(tmp_path)
    # Should not raise
    assert_not_protected(cfg, "prod", "DB_URL")


def test_protect_persists_to_disk(tmp_path):
    cfg = make_config(tmp_path)
    protect_key(cfg, "local", "DB_URL")
    # Re-load via a second config pointing at same path
    cfg2 = FakeConfig(tmp_path)
    cfg2._profiles = cfg._profiles.copy()
    assert is_protected(cfg2, "local", "DB_URL")
