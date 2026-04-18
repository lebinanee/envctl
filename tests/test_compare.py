"""Tests for envctl.compare module."""

import pytest
from unittest.mock import MagicMock
from envctl.compare import compare_profiles, format_report, CompareError, CompareEntry


def make_config(profiles: dict):
    cfg = MagicMock()
    cfg.get_profile = lambda name: profiles.get(name)
    return cfg


def test_compare_same_values():
    cfg = make_config({"local": {"A": "1"}, "staging": {"A": "1"}})
    entries = compare_profiles(cfg, "local", "staging")
    assert len(entries) == 1
    assert entries[0].status == "same"


def test_compare_changed_value():
    cfg = make_config({"local": {"A": "1"}, "staging": {"A": "2"}})
    entries = compare_profiles(cfg, "local", "staging")
    assert entries[0].status == "changed"
    assert entries[0].source_value == "1"
    assert entries[0].target_value == "2"


def test_compare_added_key():
    cfg = make_config({"local": {}, "staging": {"B": "hello"}})
    entries = compare_profiles(cfg, "local", "staging")
    assert entries[0].status == "added"
    assert entries[0].key == "B"


def test_compare_removed_key():
    cfg = make_config({"local": {"C": "val"}, "staging": {}})
    entries = compare_profiles(cfg, "local", "staging")
    assert entries[0].status == "removed"
    assert entries[0].key == "C"


def test_compare_only_diff_filters_same():
    cfg = make_config({"local": {"A": "1", "B": "2"}, "staging": {"A": "1", "B": "99"}})
    entries = compare_profiles(cfg, "local", "staging", only_diff=True)
    assert all(e.status != "same" for e in entries)
    assert len(entries) == 1


def test_compare_key_filter():
    cfg = make_config({"local": {"A": "1", "B": "2"}, "staging": {"A": "9", "B": "2"}})
    entries = compare_profiles(cfg, "local", "staging", keys=["A"])
    assert len(entries) == 1
    assert entries[0].key == "A"


def test_compare_missing_source_raises():
    cfg = make_config({"staging": {"A": "1"}})
    with pytest.raises(CompareError, match="Source profile"):
        compare_profiles(cfg, "local", "staging")


def test_compare_missing_target_raises():
    cfg = make_config({"local": {"A": "1"}})
    with pytest.raises(CompareError, match="Target profile"):
        compare_profiles(cfg, "local", "staging")


def test_format_report_no_diff():
    report = format_report([], "local", "staging")
    assert "no differences" in report


def test_format_report_contains_symbols():
    entries = [
        CompareEntry(key="A", status="added", target_value="1"),
        CompareEntry(key="B", status="removed", source_value="2"),
        CompareEntry(key="C", status="changed", source_value="x", target_value="y"),
    ]
    report = format_report(entries, "local", "staging")
    assert "+" in report
    assert "-" in report
    assert "~" in report
