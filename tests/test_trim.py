"""Tests for envctl.trim."""

from __future__ import annotations

import pytest

from envctl.trim import TrimError, TrimResult, trim_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeConfig:
    def __init__(self, profiles: dict):
        self._profiles = {k: dict(v) for k, v in profiles.items()}
        self.saved = False

    def get_profile(self, name: str):
        return self._profiles.get(name)

    def set_profile(self, name: str, data: dict):
        self._profiles[name] = dict(data)

    def save(self):
        self.saved = True


def make_config(**profiles):
    return FakeConfig(profiles)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_trim_missing_profile_raises():
    cfg = make_config()
    with pytest.raises(TrimError, match="does not exist"):
        trim_profile(cfg, "ghost")


def test_trim_all_keys():
    cfg = make_config(dev={"FOO": "  hello  ", "BAR": "world"})
    result = trim_profile(cfg, "dev")
    assert "FOO" in result.trimmed
    assert "BAR" in result.skipped
    assert cfg._profiles["dev"]["FOO"] == "hello"
    assert cfg._profiles["dev"]["BAR"] == "world"
    assert cfg.saved is True


def test_trim_specific_key():
    cfg = make_config(dev={"FOO": "  hello  ", "BAR": "  world  "})
    result = trim_profile(cfg, "dev", keys=["FOO"])
    assert "FOO" in result.trimmed
    assert "BAR" not in result.trimmed
    assert cfg._profiles["dev"]["BAR"] == "  world  "


def test_trim_missing_key_is_skipped():
    cfg = make_config(dev={"FOO": "hello"})
    result = trim_profile(cfg, "dev", keys=["MISSING"])
    assert "MISSING" in result.skipped
    assert result.total_trimmed == 0


def test_trim_no_changes_does_not_save():
    cfg = make_config(dev={"FOO": "clean"})
    result = trim_profile(cfg, "dev")
    assert result.total_trimmed == 0
    assert cfg.saved is False


def test_trim_dry_run_does_not_save():
    cfg = make_config(dev={"FOO": "  padded  "})
    result = trim_profile(cfg, "dev", dry_run=True)
    assert "FOO" in result.trimmed
    assert cfg.saved is False
    assert cfg._profiles["dev"]["FOO"] == "  padded  "


def test_trim_result_counts():
    cfg = make_config(prod={"A": " a ", "B": " b ", "C": "c"})
    result = trim_profile(cfg, "prod")
    assert result.total_trimmed == 2
    assert result.total_skipped == 1
