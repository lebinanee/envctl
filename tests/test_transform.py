"""Tests for envctl.transform."""
import pytest

from envctl.transform import (
    TransformError,
    TransformResult,
    get_transform,
    transform_profile,
)


class FakeConfig:
    def __init__(self, profiles):
        self._profiles = {k: dict(v) for k, v in profiles.items()}
        self.saved = False

    def get_profile(self, name):
        return self._profiles.get(name)

    def set_profile(self, name, vars_):
        self._profiles[name] = dict(vars_)

    def save(self):
        self.saved = True


def make_config(data):
    return FakeConfig(data)


# --- get_transform ---

def test_get_transform_upper():
    fn = get_transform("upper")
    assert fn("hello") == "HELLO"


def test_get_transform_lower():
    fn = get_transform("lower")
    assert fn("WORLD") == "world"


def test_get_transform_strip():
    fn = get_transform("strip")
    assert fn("  spaced  ") == "spaced"


def test_get_transform_trim_quotes():
    fn = get_transform("trim_quotes")
    assert fn('"quoted"') == "quoted"
    assert fn("'single'") == "single"


def test_get_transform_unknown_raises():
    with pytest.raises(TransformError, match="Unknown transform"):
        get_transform("nonexistent")


# --- transform_profile ---

def test_transform_upper_all_keys():
    cfg = make_config({"dev": {"APP_ENV": "development", "DEBUG": "true"}})
    result = transform_profile(cfg, "dev", "upper")
    assert result.applied == {"APP_ENV": "DEVELOPMENT", "DEBUG": "TRUE"}
    assert cfg._profiles["dev"]["APP_ENV"] == "DEVELOPMENT"
    assert cfg.saved


def test_transform_skips_unchanged_keys():
    cfg = make_config({"dev": {"KEY": "ALREADY_UPPER", "other": "lower"}})
    result = transform_profile(cfg, "dev", "upper")
    assert "KEY" in result.skipped
    assert "other" in result.applied


def test_transform_specific_keys_only():
    cfg = make_config({"dev": {"A": "hello", "B": "world"}})
    result = transform_profile(cfg, "dev", "upper", keys=["A"])
    assert "A" in result.applied
    assert "B" in result.skipped


def test_transform_dry_run_does_not_save():
    cfg = make_config({"dev": {"KEY": "value"}})
    result = transform_profile(cfg, "dev", "upper", dry_run=True)
    assert result.total_applied == 1
    assert not cfg.saved
    assert cfg._profiles["dev"]["KEY"] == "value"  # unchanged


def test_transform_missing_profile_raises():
    cfg = make_config({})
    with pytest.raises(TransformError, match="not found"):
        transform_profile(cfg, "ghost", "upper")


def test_transform_no_changes_returns_empty_result():
    cfg = make_config({"dev": {"KEY": "UPPER"}})
    result = transform_profile(cfg, "dev", "upper")
    assert result.total_applied == 0
    assert not cfg.saved
