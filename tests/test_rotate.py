"""Tests for envctl.rotate."""

from __future__ import annotations

import json
import pathlib
import pytest

from envctl.config import Config
from envctl.rotate import RotateError, RotateResult, rotate_key
from envctl.validate import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(tmp_path: pathlib.Path) -> Config:
    cfg_file = tmp_path / "envctl.json"
    cfg_file.write_text(json.dumps({"active_env": "local", "profiles": {}}))
    return Config(str(cfg_file))


def _make(config: Config, profile: str, vars_: dict) -> None:
    config.set_profile(profile, vars_)
    config.save()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rotate_single_profile(tmp_path):
    cfg = make_config(tmp_path)
    _make(cfg, "local", {"OLD_KEY": "value"})

    result = rotate_key(cfg, "OLD_KEY", "NEW_KEY", profile="local")

    assert result.updated == ["local"]
    assert result.skipped == []
    assert result.total_updated == 1
    vars_ = cfg.get_profile("local")
    assert "NEW_KEY" in vars_
    assert vars_["NEW_KEY"] == "value"
    assert "OLD_KEY" not in vars_


def test_rotate_all_profiles(tmp_path):
    cfg = make_config(tmp_path)
    _make(cfg, "local", {"TOKEN": "abc"})
    _make(cfg, "staging", {"TOKEN": "xyz"})

    result = rotate_key(cfg, "TOKEN", "API_TOKEN")

    assert set(result.updated) == {"local", "staging"}
    assert cfg.get_profile("local")["API_TOKEN"] == "abc"
    assert cfg.get_profile("staging")["API_TOKEN"] == "xyz"


def test_rotate_skips_profile_missing_old_key(tmp_path):
    cfg = make_config(tmp_path)
    _make(cfg, "local", {"OTHER": "1"})
    _make(cfg, "staging", {"OLD_KEY": "2"})

    result = rotate_key(cfg, "OLD_KEY", "NEW_KEY")

    assert "staging" in result.updated
    assert "local" in result.skipped


def test_rotate_skips_existing_new_key_without_overwrite(tmp_path):
    cfg = make_config(tmp_path)
    _make(cfg, "local", {"OLD_KEY": "old", "NEW_KEY": "existing"})

    result = rotate_key(cfg, "OLD_KEY", "NEW_KEY", profile="local")

    assert result.skipped == ["local"]
    assert result.updated == []
    assert cfg.get_profile("local")["NEW_KEY"] == "existing"


def test_rotate_overwrites_when_flag_set(tmp_path):
    cfg = make_config(tmp_path)
    _make(cfg, "local", {"OLD_KEY": "fresh", "NEW_KEY": "stale"})

    result = rotate_key(cfg, "OLD_KEY", "NEW_KEY", profile="local", overwrite=True)

    assert result.updated == ["local"]
    assert cfg.get_profile("local")["NEW_KEY"] == "fresh"


def test_rotate_invalid_new_key_raises(tmp_path):
    cfg = make_config(tmp_path)
    _make(cfg, "local", {"OLD_KEY": "v"})

    with pytest.raises(ValidationError):
        rotate_key(cfg, "OLD_KEY", "invalid-key", profile="local")


def test_rotate_missing_profile_raises(tmp_path):
    cfg = make_config(tmp_path)

    with pytest.raises(RotateError, match="does not exist"):
        rotate_key(cfg, "OLD_KEY", "NEW_KEY", profile="nonexistent")
