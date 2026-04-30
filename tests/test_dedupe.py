"""Tests for envctl.dedupe."""

from __future__ import annotations

from typing import Dict, Optional

import pytest

from envctl.dedupe import DedupeError, dedupe_profile


# ---------------------------------------------------------------------------
# Minimal fake config
# ---------------------------------------------------------------------------

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


def make_config(profile_vars: Dict[str, str]) -> FakeConfig:
    return FakeConfig({"dev": profile_vars})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_dedupe_no_duplicates():
    cfg = make_config({"A": "1", "B": "2", "C": "3"})
    result = dedupe_profile(cfg, "dev")
    assert result.total_removed == 0
    assert result.removed == []
    assert not cfg.saved


def test_dedupe_removes_duplicate_value():
    cfg = make_config({"A": "same", "B": "other", "C": "same"})
    result = dedupe_profile(cfg, "dev")
    assert result.total_removed == 1
    assert "C" in result.removed
    assert "A" not in result.removed
    assert cfg.saved
    assert "C" not in cfg.get_profile("dev")


def test_dedupe_multiple_duplicates():
    cfg = make_config({"A": "x", "B": "x", "C": "x"})
    result = dedupe_profile(cfg, "dev")
    assert result.total_removed == 2
    assert set(result.removed) == {"B", "C"}
    assert cfg.get_profile("dev") == {"A": "x"}


def test_dedupe_dry_run_does_not_save():
    cfg = make_config({"A": "dup", "B": "dup"})
    result = dedupe_profile(cfg, "dev", dry_run=True)
    assert result.total_removed == 1
    assert "B" in result.removed
    assert not cfg.saved
    assert "B" in cfg.get_profile("dev")


def test_dedupe_with_keys_filter():
    cfg = make_config({"A": "val", "B": "val", "C": "val"})
    result = dedupe_profile(cfg, "dev", keys=["A", "B"])
    # Only A and B are candidates; C is skipped
    assert result.total_removed == 1
    assert "B" in result.removed
    assert "C" in result.skipped
    # C must still be present
    assert "C" in cfg.get_profile("dev")


def test_dedupe_missing_profile_raises():
    cfg = FakeConfig({})
    with pytest.raises(DedupeError, match="not found"):
        dedupe_profile(cfg, "nonexistent")
