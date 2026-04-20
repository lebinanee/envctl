"""Unit tests for envctl.merge."""

from __future__ import annotations

import json
import pathlib
import pytest

from envctl.config import Config
from envctl.merge import MergeError, merge_profiles


def make_config(tmp_path: pathlib.Path) -> Config:
    cfg_file = tmp_path / "envctl.json"
    data = {
        "active": "local",
        "profiles": {
            "local": {"vars": {"FOO": "foo", "BAR": "bar"}},
            "staging": {"vars": {"FOO": "foo_stg", "BAZ": "baz"}},
            "production": {"vars": {}},
        },
    }
    cfg_file.write_text(json.dumps(data))
    return Config(path=str(cfg_file))


def _get_vars(cfg: Config, profile: str) -> dict:
    return cfg._load()["profiles"][profile]["vars"]


def test_merge_adds_new_keys(tmp_path):
    cfg = make_config(tmp_path)
    result = merge_profiles(cfg, src="staging", dst="production")
    assert "FOO" in result.added
    assert "BAZ" in result.added
    assert _get_vars(cfg, "production")["FOO"] == "foo_stg"


def test_merge_skips_identical_keys(tmp_path):
    cfg = make_config(tmp_path)
    # FOO exists in both local and staging but with different values; BAR only in local
    result = merge_profiles(cfg, src="local", dst="staging")
    assert "BAR" in result.added
    assert "FOO" in result.conflicts  # different value, no overwrite


def test_merge_conflict_without_overwrite(tmp_path):
    cfg = make_config(tmp_path)
    result = merge_profiles(cfg, src="staging", dst="local")
    assert "FOO" in result.conflicts
    assert _get_vars(cfg, "local")["FOO"] == "foo"  # unchanged


def test_merge_overwrite_resolves_conflict(tmp_path):
    cfg = make_config(tmp_path)
    result = merge_profiles(cfg, src="staging", dst="local", overwrite=True)
    assert "FOO" in result.updated
    assert _get_vars(cfg, "local")["FOO"] == "foo_stg"


def test_merge_specific_keys(tmp_path):
    cfg = make_config(tmp_path)
    result = merge_profiles(cfg, src="staging", dst="production", keys=["BAZ"])
    vars_ = _get_vars(cfg, "production")
    assert "BAZ" in vars_
    assert "FOO" not in vars_
    assert result.added == ["BAZ"]


def test_merge_missing_key_in_src_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(MergeError, match="NOPE"):
        merge_profiles(cfg, src="staging", dst="production", keys=["NOPE"])


def test_merge_missing_src_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(MergeError, match="ghost"):
        merge_profiles(cfg, src="ghost", dst="production")


def test_merge_missing_dst_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(MergeError, match="nowhere"):
        merge_profiles(cfg, src="staging", dst="nowhere")


def test_merge_dry_run_makes_no_changes(tmp_path):
    cfg = make_config(tmp_path)
    before = _get_vars(cfg, "production").copy()
    result = merge_profiles(cfg, src="staging", dst="production", dry_run=True)
    assert _get_vars(cfg, "production") == before
    assert result.total_changes > 0  # would have changed


def test_merge_skipped_identical_values(tmp_path):
    cfg = make_config(tmp_path)
    # staging -> staging: everything identical, nothing to do
    result = merge_profiles(cfg, src="staging", dst="staging")
    assert result.total_changes == 0
    assert len(result.skipped) == len(_get_vars(cfg, "staging"))
