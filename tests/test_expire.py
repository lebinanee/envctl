"""Tests for envctl.expire module."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envctl.expire import (
    ExpireError,
    ExpiryEntry,
    get_expired,
    list_expiries,
    remove_expiry,
    set_expiry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeConfig:
    def __init__(self, tmp_path: Path, profiles: dict):
        self.path = str(tmp_path / "envctl.json")
        self._profiles = profiles

    def get_profile(self, name: str):
        return self._profiles.get(name)


def make_config(tmp_path: Path, profiles=None):
    profiles = profiles or {"local": {"API_KEY": "abc", "DB_URL": "postgres://"}}
    return _FakeConfig(tmp_path, profiles)


def _expiry_path(tmp_path: Path) -> Path:
    return tmp_path / ".envctl_expiry.json"


def _future() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=30)


def _past() -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=1)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_set_expiry_creates_file(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    entry = set_expiry(cfg, "local", "API_KEY", _future(), expiry_path=ep)
    assert ep.exists()
    assert entry.key == "API_KEY"
    assert entry.profile == "local"


def test_set_expiry_missing_key_raises(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    with pytest.raises(ExpireError, match="MISSING_KEY"):
        set_expiry(cfg, "local", "MISSING_KEY", _future(), expiry_path=ep)


def test_set_expiry_missing_profile_raises(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    with pytest.raises(ExpireError):
        set_expiry(cfg, "production", "API_KEY", _future(), expiry_path=ep)


def test_set_expiry_overwrites_existing(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    t1 = _future()
    t2 = _future() + timedelta(days=10)
    set_expiry(cfg, "local", "API_KEY", t1, expiry_path=ep)
    set_expiry(cfg, "local", "API_KEY", t2, expiry_path=ep)
    entries = list_expiries(cfg, "local", expiry_path=ep)
    api_entries = [e for e in entries if e.key == "API_KEY"]
    assert len(api_entries) == 1
    assert api_entries[0].expires_at == t2


def test_get_expired_returns_only_past(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    set_expiry(cfg, "local", "API_KEY", _past(), expiry_path=ep)
    set_expiry(cfg, "local", "DB_URL", _future(), expiry_path=ep)
    expired = get_expired(cfg, "local", expiry_path=ep)
    assert len(expired) == 1
    assert expired[0].key == "API_KEY"


def test_get_expired_empty_when_none_past(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    set_expiry(cfg, "local", "API_KEY", _future(), expiry_path=ep)
    assert get_expired(cfg, "local", expiry_path=ep) == []


def test_remove_expiry_returns_true(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    set_expiry(cfg, "local", "API_KEY", _future(), expiry_path=ep)
    assert remove_expiry(cfg, "local", "API_KEY", expiry_path=ep) is True
    assert list_expiries(cfg, "local", expiry_path=ep) == []


def test_remove_expiry_returns_false_when_absent(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    assert remove_expiry(cfg, "local", "API_KEY", expiry_path=ep) is False


def test_list_expiries_empty_when_no_file(tmp_path):
    cfg = make_config(tmp_path)
    ep = _expiry_path(tmp_path)
    assert list_expiries(cfg, "local", expiry_path=ep) == []


def test_entry_is_expired_flag(tmp_path):
    past_entry = ExpiryEntry("local", "K", _past())
    future_entry = ExpiryEntry("local", "K", _future())
    assert past_entry.is_expired() is True
    assert future_entry.is_expired() is False
