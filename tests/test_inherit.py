"""Tests for envctl.inherit."""

from __future__ import annotations

import pytest

from envctl.inherit import InheritError, inherit_profile


# ---------------------------------------------------------------------------
# Minimal fake Config
# ---------------------------------------------------------------------------

class FakeConfig:
    def __init__(self, profiles: dict):
        self._profiles = {k: dict(v) for k, v in profiles.items()}
        self.saved = False

    def get_profile(self, name: str):
        return dict(self._profiles[name]) if name in self._profiles else None

    def set_profile(self, name: str, vars_: dict):
        self._profiles[name] = dict(vars_)

    def save(self):
        self.saved = True


def make_config(base_vars=None, child_vars=None):
    return FakeConfig({
        "base": base_vars or {},
        "child": child_vars or {},
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_inherit_adds_new_keys():
    cfg = make_config(base_vars={"FOO": "1", "BAR": "2"}, child_vars={})
    result = inherit_profile(cfg, "base", "child")
    assert sorted(result.inherited) == ["BAR", "FOO"]
    assert result.skipped == []
    assert result.overwritten == []
    assert cfg._profiles["child"] == {"FOO": "1", "BAR": "2"}
    assert cfg.saved


def test_inherit_skips_existing_keys_without_overwrite():
    cfg = make_config(base_vars={"FOO": "base_val"}, child_vars={"FOO": "child_val"})
    result = inherit_profile(cfg, "base", "child")
    assert result.inherited == []
    assert result.skipped == ["FOO"]
    assert cfg._profiles["child"]["FOO"] == "child_val"


def test_inherit_overwrites_when_flag_set():
    cfg = make_config(base_vars={"FOO": "new"}, child_vars={"FOO": "old"})
    result = inherit_profile(cfg, "base", "child", overwrite=True)
    assert result.overwritten == ["FOO"]
    assert cfg._profiles["child"]["FOO"] == "new"


def test_inherit_specific_keys_only():
    cfg = make_config(base_vars={"A": "1", "B": "2", "C": "3"}, child_vars={})
    result = inherit_profile(cfg, "base", "child", keys=["A", "C"])
    assert sorted(result.inherited) == ["A", "C"]
    assert "B" not in cfg._profiles["child"]


def test_inherit_dry_run_does_not_save():
    cfg = make_config(base_vars={"FOO": "1"}, child_vars={})
    result = inherit_profile(cfg, "base", "child", dry_run=True)
    assert result.inherited == ["FOO"]
    assert cfg._profiles["child"] == {}  # unchanged
    assert not cfg.saved


def test_inherit_missing_base_raises():
    cfg = make_config()
    del cfg._profiles["base"]
    with pytest.raises(InheritError, match="Base profile 'base' does not exist"):
        inherit_profile(cfg, "base", "child")


def test_inherit_missing_child_raises():
    cfg = make_config()
    del cfg._profiles["child"]
    with pytest.raises(InheritError, match="Child profile 'child' does not exist"):
        inherit_profile(cfg, "base", "child")


def test_inherit_key_not_in_base_is_silently_skipped():
    cfg = make_config(base_vars={"FOO": "1"}, child_vars={})
    result = inherit_profile(cfg, "base", "child", keys=["FOO", "MISSING"])
    assert result.inherited == ["FOO"]
    assert result.total_changes == 1
