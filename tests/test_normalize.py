"""Tests for envctl.normalize."""
from __future__ import annotations

import pytest

from envctl.normalize import NormalizeError, get_strategy, normalize_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeConfig:
    def __init__(self, profiles=None):
        self._profiles = profiles or {}
        self.saved = False

    def get_profile(self, name):
        return dict(self._profiles.get(name, {})) if name in self._profiles else None

    def set_profile(self, name, data):
        self._profiles[name] = dict(data)

    def save(self):
        self.saved = True


def make_config(**profiles):
    return FakeConfig(profiles)


# ---------------------------------------------------------------------------
# get_strategy
# ---------------------------------------------------------------------------

def test_get_strategy_valid():
    fn = get_strategy("upper")
    assert fn("hello") == "HELLO"


def test_get_strategy_unknown_raises():
    with pytest.raises(NormalizeError, match="Unknown strategy"):
        get_strategy("camel")


# ---------------------------------------------------------------------------
# normalize_profile
# ---------------------------------------------------------------------------

def test_normalize_upper():
    cfg = make_config(dev={"KEY": "hello", "OTHER": "world"})
    result = normalize_profile(cfg, "dev", "upper")
    assert result.applied == {"KEY": "HELLO", "OTHER": "WORLD"}
    assert cfg._profiles["dev"] == {"KEY": "HELLO", "OTHER": "WORLD"}


def test_normalize_lower():
    cfg = make_config(dev={"KEY": "HELLO"})
    result = normalize_profile(cfg, "dev", "lower")
    assert result.applied == {"KEY": "hello"}


def test_normalize_strip():
    cfg = make_config(dev={"KEY": "  spaced  ", "CLEAN": "ok"})
    result = normalize_profile(cfg, "dev", "strip")
    assert "KEY" in result.applied
    assert result.applied["KEY"] == "spaced"
    assert "CLEAN" in result.skipped


def test_normalize_specific_keys():
    cfg = make_config(dev={"A": "hello", "B": "world"})
    result = normalize_profile(cfg, "dev", "upper", keys=["A"])
    assert "A" in result.applied
    assert "B" not in result.applied


def test_normalize_dry_run_does_not_save():
    cfg = make_config(dev={"KEY": "hello"})
    result = normalize_profile(cfg, "dev", "upper", dry_run=True)
    assert result.applied == {"KEY": "HELLO"}
    assert not cfg.saved
    assert cfg._profiles["dev"]["KEY"] == "hello"  # unchanged


def test_normalize_missing_profile_raises():
    cfg = make_config()
    with pytest.raises(NormalizeError, match="not found"):
        normalize_profile(cfg, "ghost", "upper")


def test_normalize_missing_key_skipped():
    cfg = make_config(dev={"A": "val"})
    result = normalize_profile(cfg, "dev", "upper", keys=["A", "MISSING"])
    assert "MISSING" in result.skipped
    assert result.skipped["MISSING"] == "key not found"


def test_normalize_saves_when_changes_exist():
    cfg = make_config(dev={"KEY": "hello"})
    normalize_profile(cfg, "dev", "upper")
    assert cfg.saved


def test_normalize_no_save_when_no_changes():
    cfg = make_config(dev={"KEY": "HELLO"})
    normalize_profile(cfg, "dev", "upper")
    assert not cfg.saved
