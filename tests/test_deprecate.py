"""Tests for envctl.deprecate."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Dict

import pytest

from envctl.deprecate import (
    DeprecateError,
    mark_deprecated,
    unmark_deprecated,
    list_deprecated,
    check_deprecated,
)


def make_config(tmp_path: Path, profiles: Dict[str, dict]):
    cfg_file = tmp_path / "envctl.json"
    cfg_file.write_text("{}")

    class FakeConfig:
        path = str(cfg_file)

        def get_profile(self, name):
            return profiles.get(name)

    return FakeConfig()


def test_mark_deprecated_success(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"OLD_KEY": "val"}})
    entry = mark_deprecated(cfg, "dev", "OLD_KEY", "Use NEW_KEY instead", replacement="NEW_KEY")
    assert entry.key == "OLD_KEY"
    assert entry.profile == "dev"
    assert entry.reason == "Use NEW_KEY instead"
    assert entry.replacement == "NEW_KEY"


def test_mark_deprecated_persists(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"OLD_KEY": "val"}})
    mark_deprecated(cfg, "dev", "OLD_KEY", "deprecated")
    dep_file = tmp_path / ".envctl_deprecations.json"
    assert dep_file.exists()
    data = json.loads(dep_file.read_text())
    assert len(data) == 1
    assert data[0]["key"] == "OLD_KEY"


def test_mark_deprecated_missing_profile_raises(tmp_path):
    cfg = make_config(tmp_path, {})
    with pytest.raises(DeprecateError, match="Profile"):
        mark_deprecated(cfg, "ghost", "X", "reason")


def test_mark_deprecated_missing_key_raises(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"OTHER": "v"}})
    with pytest.raises(DeprecateError, match="Key"):
        mark_deprecated(cfg, "dev", "MISSING", "reason")


def test_mark_deprecated_replaces_existing(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"OLD_KEY": "val"}})
    mark_deprecated(cfg, "dev", "OLD_KEY", "first reason")
    mark_deprecated(cfg, "dev", "OLD_KEY", "updated reason", replacement="NEW")
    entries = list_deprecated(cfg, profile="dev")
    assert len(entries) == 1
    assert entries[0].reason == "updated reason"
    assert entries[0].replacement == "NEW"


def test_unmark_deprecated_success(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"OLD_KEY": "val"}})
    mark_deprecated(cfg, "dev", "OLD_KEY", "deprecated")
    removed = unmark_deprecated(cfg, "dev", "OLD_KEY")
    assert removed is True
    assert list_deprecated(cfg, profile="dev") == []


def test_unmark_deprecated_not_found_returns_false(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"A": "1"}})
    result = unmark_deprecated(cfg, "dev", "NONEXISTENT")
    assert result is False


def test_list_deprecated_filters_by_profile(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"A": "1"}, "prod": {"B": "2"}})
    mark_deprecated(cfg, "dev", "A", "old")
    mark_deprecated(cfg, "prod", "B", "old")
    dev_entries = list_deprecated(cfg, profile="dev")
    assert len(dev_entries) == 1
    assert dev_entries[0].profile == "dev"


def test_check_deprecated_returns_only_present_keys(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"A": "1"}})
    mark_deprecated(cfg, "dev", "A", "going away")
    result = check_deprecated(cfg, "dev")
    assert "A" in result
    assert result["A"].reason == "going away"


def test_check_deprecated_excludes_removed_keys(tmp_path):
    profiles = {"dev": {"A": "1"}}
    cfg = make_config(tmp_path, profiles)
    mark_deprecated(cfg, "dev", "A", "old")
    # Simulate key removed from profile
    profiles["dev"].pop("A")
    result = check_deprecated(cfg, "dev")
    assert result == {}
