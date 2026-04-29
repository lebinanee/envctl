"""Tests for envctl.prune."""

from __future__ import annotations

from typing import Dict, Optional

import pytest

from envctl.prune import PruneError, prune_profile


class FakeConfig:
    def __init__(self, profiles: Dict[str, Dict[str, str]]) -> None:
        self._profiles = {k: dict(v) for k, v in profiles.items()}
        self.saved = False

    def get_profile(self, name: str) -> Optional[Dict[str, str]]:
        return self._profiles.get(name)

    def set_profile(self, name: str, vars_: Dict[str, str]) -> None:
        self._profiles[name] = dict(vars_)

    def save(self) -> None:
        self.saved = True


def make_config(vars_: Dict[str, str], profile: str = "dev") -> FakeConfig:
    return FakeConfig({profile: vars_})


def test_prune_removes_empty_values():
    cfg = make_config({"A": "hello", "B": "", "C": "world"})
    result = prune_profile(cfg, "dev")
    assert "B" in result.removed
    assert "A" in result.skipped
    assert "C" in result.skipped
    assert cfg.get_profile("dev") == {"A": "hello", "C": "world"}


def test_prune_removes_whitespace_only():
    cfg = make_config({"X": "   ", "Y": "ok"})
    result = prune_profile(cfg, "dev")
    assert "X" in result.removed
    assert "Y" in result.skipped


def test_prune_specific_keys():
    cfg = make_config({"A": "", "B": "", "C": "val"})
    result = prune_profile(cfg, "dev", keys=["A"])
    assert result.removed == ["A"]
    assert cfg.get_profile("dev") == {"B": "", "C": "val"}


def test_prune_missing_key_in_keys_list_is_skipped():
    cfg = make_config({"A": ""})
    result = prune_profile(cfg, "dev", keys=["A", "MISSING"])
    assert "MISSING" in result.skipped
    assert "A" in result.removed


def test_prune_dry_run_does_not_save():
    cfg = make_config({"A": ""})
    result = prune_profile(cfg, "dev", dry_run=True)
    assert result.total_removed == 1
    assert not cfg.saved
    assert cfg.get_profile("dev") == {"A": ""}


def test_prune_saves_on_changes():
    cfg = make_config({"A": ""})
    prune_profile(cfg, "dev")
    assert cfg.saved


def test_prune_no_changes_does_not_save():
    cfg = make_config({"A": "value"})
    prune_profile(cfg, "dev")
    assert not cfg.saved


def test_prune_missing_profile_raises():
    cfg = make_config({})
    with pytest.raises(PruneError, match="does not exist"):
        prune_profile(cfg, "nonexistent")


def test_prune_totals():
    cfg = make_config({"A": "", "B": " ", "C": "ok"})
    result = prune_profile(cfg, "dev")
    assert result.total_removed == 2
    assert result.total_skipped == 1
