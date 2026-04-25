"""Tests for envctl.cascade."""

from __future__ import annotations

import pytest

from envctl.cascade import CascadeError, CascadeResult, cascade_profiles, format_cascade_report


class FakeConfig:
    def __init__(self, profiles: dict):
        self._profiles = profiles

    def get_profile(self, name: str):
        return self._profiles.get(name)


def make_config(**profiles):
    return FakeConfig(profiles)


# ---------------------------------------------------------------------------
# cascade_profiles
# ---------------------------------------------------------------------------

def test_cascade_no_profiles_raises():
    cfg = make_config(base={"A": "1"})
    with pytest.raises(CascadeError, match="At least one"):
        cascade_profiles(cfg, [])


def test_cascade_missing_profile_raises():
    cfg = make_config(base={"A": "1"})
    with pytest.raises(CascadeError, match="'staging' not found"):
        cascade_profiles(cfg, ["base", "staging"])


def test_cascade_single_profile():
    cfg = make_config(base={"A": "1", "B": "2"})
    result = cascade_profiles(cfg, ["base"])
    assert result.effective == {"A": "1", "B": "2"}
    assert result.sources == {"A": "base", "B": "base"}
    assert result.overridden == {}


def test_cascade_override_later_profile_wins():
    cfg = make_config(
        base={"A": "base_val", "B": "shared"},
        prod={"A": "prod_val", "C": "only_prod"},
    )
    result = cascade_profiles(cfg, ["base", "prod"])
    assert result.effective["A"] == "prod_val"
    assert result.effective["B"] == "shared"
    assert result.effective["C"] == "only_prod"
    assert result.sources["A"] == "prod"
    assert "A" in result.overridden
    assert result.overridden["A"] == ["base", "prod"]


def test_cascade_key_filter():
    cfg = make_config(base={"A": "1", "B": "2", "C": "3"})
    result = cascade_profiles(cfg, ["base"], keys=["A", "C"])
    assert set(result.effective.keys()) == {"A", "C"}


def test_cascade_three_layers():
    cfg = make_config(
        base={"X": "base"},
        staging={"X": "staging"},
        prod={"X": "prod"},
    )
    result = cascade_profiles(cfg, ["base", "staging", "prod"])
    assert result.effective["X"] == "prod"
    assert len(result.overridden["X"]) == 3


def test_cascade_empty_profile():
    cfg = make_config(base={}, override={"K": "v"})
    result = cascade_profiles(cfg, ["base", "override"])
    assert result.effective == {"K": "v"}


# ---------------------------------------------------------------------------
# format_cascade_report
# ---------------------------------------------------------------------------

def test_format_report_empty():
    result = CascadeResult()
    assert format_cascade_report(result) == "No variables resolved."


def test_format_report_shows_source():
    cfg = make_config(base={"A": "1"})
    result = cascade_profiles(cfg, ["base"])
    report = format_cascade_report(result)
    assert "A=1" in report
    assert "[from: base]" in report


def test_format_report_shows_override_note():
    cfg = make_config(base={"A": "old"}, prod={"A": "new"})
    result = cascade_profiles(cfg, ["base", "prod"])
    report = format_cascade_report(result)
    assert "overrode: base" in report
