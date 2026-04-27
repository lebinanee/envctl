"""Tests for envctl.reorder."""
from __future__ import annotations

import pytest

from envctl.reorder import ReorderError, reorder_profile


# ---------------------------------------------------------------------------
# Minimal fake config
# ---------------------------------------------------------------------------

class _FakeConfig:
    def __init__(self, profiles: dict):
        self._data = {"profiles": {k: dict(v) for k, v in profiles.items()}}
        self._saved = False

    def get_profile(self, name: str):
        return self._data["profiles"].get(name)

    def save(self):
        self._saved = True


def make_config(profile_vars: dict) -> _FakeConfig:
    return _FakeConfig({"dev": profile_vars})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_reorder_alphabetical():
    cfg = make_config({"ZEBRA": "1", "APPLE": "2", "MANGO": "3"})
    result = reorder_profile(cfg, "dev", alphabetical=True)
    assert result.new_order == ["APPLE", "MANGO", "ZEBRA"]
    assert result.changed
    assert cfg._saved


def test_reorder_alphabetical_reverse():
    cfg = make_config({"ZEBRA": "1", "APPLE": "2", "MANGO": "3"})
    result = reorder_profile(cfg, "dev", alphabetical=True, reverse=True)
    assert result.new_order == ["ZEBRA", "MANGO", "APPLE"]


def test_reorder_custom_keys():
    cfg = make_config({"C": "3", "A": "1", "B": "2"})
    result = reorder_profile(cfg, "dev", keys=["A", "B", "C"])
    assert result.new_order == ["A", "B", "C"]


def test_reorder_custom_keys_unknown_appended():
    cfg = make_config({"C": "3", "A": "1", "B": "2", "D": "4"})
    result = reorder_profile(cfg, "dev", keys=["A", "C"])
    # B and D not in keys list — appended in original relative order
    assert result.new_order[:2] == ["A", "C"]
    assert set(result.new_order[2:]) == {"B", "D"}


def test_reorder_unchanged_when_already_sorted():
    cfg = make_config({"A": "1", "B": "2", "C": "3"})
    result = reorder_profile(cfg, "dev", alphabetical=True)
    assert not result.changed


def test_reorder_missing_profile_raises():
    cfg = make_config({})
    with pytest.raises(ReorderError, match="not found"):
        reorder_profile(cfg, "nonexistent", alphabetical=True)


def test_reorder_result_original_order_preserved():
    original = {"Z": "1", "A": "2", "M": "3"}
    cfg = make_config(original)
    result = reorder_profile(cfg, "dev", alphabetical=True)
    assert result.original_order == ["Z", "A", "M"]


def test_reorder_reverse_only():
    cfg = make_config({"A": "1", "B": "2", "C": "3"})
    result = reorder_profile(cfg, "dev", reverse=True)
    assert result.new_order == ["C", "B", "A"]
