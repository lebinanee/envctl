"""Tests for envctl/diff.py"""

import json
import pytest
from pathlib import Path

from envctl.config import Config
from envctl.diff import DiffError, DiffEntry, DiffResult, diff_profiles, format_diff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(tmp_path: Path) -> Config:
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"active_env": "local", "profiles": {}}))
    return Config(str(cfg_file))


def _set(config: Config, profile: str, vars_: dict) -> None:
    data = config._load()
    data.setdefault("profiles", {})[profile] = vars_
    config.save(data)


# ---------------------------------------------------------------------------
# diff_profiles tests
# ---------------------------------------------------------------------------

def test_diff_added_key(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {"A": "1"})
    _set(cfg, "staging", {"A": "1", "B": "2"})
    result = diff_profiles(cfg, "local", "staging")
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["B"] == "added"
    assert statuses["A"] == "changed" or statuses.get("A") is None or statuses["A"] != "added"


def test_diff_removed_key(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {"A": "1", "B": "2"})
    _set(cfg, "staging", {"A": "1"})
    result = diff_profiles(cfg, "local", "staging")
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["B"] == "removed"


def test_diff_changed_key(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {"URL": "http://localhost"})
    _set(cfg, "staging", {"URL": "https://staging.example.com"})
    result = diff_profiles(cfg, "local", "staging")
    assert result.entries[0].status == "changed"
    assert result.entries[0].left_value == "http://localhost"
    assert result.entries[0].right_value == "https://staging.example.com"


def test_diff_unchanged_excluded_by_default(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {"A": "1"})
    _set(cfg, "staging", {"A": "1"})
    result = diff_profiles(cfg, "local", "staging", show_unchanged=False)
    assert result.entries == []


def test_diff_unchanged_included_when_flag_set(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {"A": "1"})
    _set(cfg, "staging", {"A": "1"})
    result = diff_profiles(cfg, "local", "staging", show_unchanged=True)
    assert any(e.status == "unchanged" for e in result.entries)


def test_diff_invalid_left_profile_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(DiffError, match="Unknown profile"):
        diff_profiles(cfg, "nope", "staging")


def test_diff_invalid_right_profile_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(DiffError, match="Unknown profile"):
        diff_profiles(cfg, "local", "nope")


def test_diff_has_changes_true(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {"X": "1"})
    _set(cfg, "staging", {"X": "2"})
    result = diff_profiles(cfg, "local", "staging")
    assert result.has_changes is True


def test_diff_has_changes_false(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {"X": "1"})
    _set(cfg, "staging", {"X": "1"})
    result = diff_profiles(cfg, "local", "staging")
    assert result.has_changes is False


def test_format_diff_contains_summary(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {"A": "1"})
    _set(cfg, "staging", {"A": "2", "B": "3"})
    result = diff_profiles(cfg, "local", "staging")
    report = format_diff(result)
    assert "local -> staging" in report
    assert "+1" in report   # B added
    assert "~1" in report   # A changed


def test_format_diff_empty_profiles(tmp_path):
    cfg = make_config(tmp_path)
    _set(cfg, "local", {})
    _set(cfg, "staging", {})
    result = diff_profiles(cfg, "local", "staging")
    report = format_diff(result)
    assert "(no entries)" in report
