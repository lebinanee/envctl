"""Tests for envctl.ttl module."""
import json
import time
from pathlib import Path

import pytest

from envctl.ttl import (
    TTLError,
    TTLEntry,
    set_ttl,
    get_ttl,
    purge_expired,
    list_ttls,
    TTL_FILE,
)


class FakeConfig:
    def __init__(self, tmp_path: Path):
        self.path = str(tmp_path / "config.json")
        self._data: dict = {}

    def get_profile(self, profile: str) -> dict:
        return dict(self._data.get(profile, {}))

    def set_profile(self, profile: str, vars_: dict) -> None:
        self._data[profile] = dict(vars_)

    def save(self) -> None:
        pass


def make_config(tmp_path, profiles=None):
    cfg = FakeConfig(tmp_path)
    for profile, vars_ in (profiles or {}).items():
        cfg.set_profile(profile, vars_)
    return cfg


def test_set_ttl_creates_entry(tmp_path):
    cfg = make_config(tmp_path, {"local": {"DB_URL": "sqlite"}})
    entry = set_ttl(cfg, "local", "DB_URL", seconds=3600)
    assert entry.key == "DB_URL"
    assert entry.profile == "local"
    assert not entry.is_expired()


def test_set_ttl_missing_key_raises(tmp_path):
    cfg = make_config(tmp_path, {"local": {}})
    with pytest.raises(TTLError, match="not found"):
        set_ttl(cfg, "local", "MISSING", seconds=60)


def test_get_ttl_returns_none_when_not_set(tmp_path):
    cfg = make_config(tmp_path, {"local": {"KEY": "val"}})
    assert get_ttl(cfg, "local", "KEY") is None


def test_get_ttl_returns_entry_after_set(tmp_path):
    cfg = make_config(tmp_path, {"local": {"API_KEY": "secret"}})
    set_ttl(cfg, "local", "API_KEY", seconds=100)
    entry = get_ttl(cfg, "local", "API_KEY")
    assert entry is not None
    assert entry.key == "API_KEY"


def test_list_ttls_empty(tmp_path):
    cfg = make_config(tmp_path, {"local": {}})
    assert list_ttls(cfg, "local") == []


def test_list_ttls_multiple(tmp_path):
    cfg = make_config(tmp_path, {"local": {"A": "1", "B": "2"}})
    set_ttl(cfg, "local", "A", seconds=60)
    set_ttl(cfg, "local", "B", seconds=120)
    entries = list_ttls(cfg, "local")
    assert len(entries) == 2
    assert {e.key for e in entries} == {"A", "B"}


def test_purge_expired_removes_key(tmp_path):
    cfg = make_config(tmp_path, {"local": {"TEMP": "value"}})
    cfg._data["local"]["TEMP"] = "value"  # ensure present
    set_ttl(cfg, "local", "TEMP", seconds=0)
    time.sleep(0.05)  # let it expire
    removed = purge_expired(cfg, "local")
    assert "TEMP" in removed


def test_purge_expired_no_expired(tmp_path):
    cfg = make_config(tmp_path, {"local": {"KEEP": "val"}})
    set_ttl(cfg, "local", "KEEP", seconds=3600)
    removed = purge_expired(cfg, "local")
    assert removed == []


def test_set_ttl_overwrites_previous(tmp_path):
    cfg = make_config(tmp_path, {"local": {"X": "1"}})
    set_ttl(cfg, "local", "X", seconds=10)
    set_ttl(cfg, "local", "X", seconds=9999)
    entries = list_ttls(cfg, "local")
    assert len(entries) == 1
