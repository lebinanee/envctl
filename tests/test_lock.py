"""Tests for envctl.lock."""
import json
import pytest
from pathlib import Path

from envctl.lock import (
    LockError,
    lock_profile,
    unlock_profile,
    is_locked,
    list_locked,
    assert_unlocked,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(tmp_path: Path):
    """Return a minimal Config-like object backed by a temp directory."""
    import types

    cfg_file = tmp_path / "envctl.json"
    data = {"active": "local", "envs": {"local": {}, "staging": {}, "production": {}}}
    cfg_file.write_text(json.dumps(data))

    obj = types.SimpleNamespace()
    obj.path = str(cfg_file)
    obj.config = data
    return obj


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_lock_profile_success(tmp_path):
    cfg = make_config(tmp_path)
    result = lock_profile(cfg, "staging")
    assert result is True
    assert is_locked(cfg, "staging") is True


def test_lock_profile_already_locked(tmp_path):
    cfg = make_config(tmp_path)
    lock_profile(cfg, "staging")
    result = lock_profile(cfg, "staging")
    assert result is False


def test_lock_missing_profile_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(LockError, match="does not exist"):
        lock_profile(cfg, "nonexistent")


def test_unlock_profile_success(tmp_path):
    cfg = make_config(tmp_path)
    lock_profile(cfg, "production")
    result = unlock_profile(cfg, "production")
    assert result is True
    assert is_locked(cfg, "production") is False


def test_unlock_not_locked_returns_false(tmp_path):
    cfg = make_config(tmp_path)
    result = unlock_profile(cfg, "local")
    assert result is False


def test_list_locked_empty(tmp_path):
    cfg = make_config(tmp_path)
    assert list_locked(cfg) == []


def test_list_locked_multiple(tmp_path):
    cfg = make_config(tmp_path)
    lock_profile(cfg, "production")
    lock_profile(cfg, "staging")
    assert list_locked(cfg) == ["production", "staging"]


def test_assert_unlocked_passes_when_not_locked(tmp_path):
    cfg = make_config(tmp_path)
    # Should not raise
    assert_unlocked(cfg, "local")


def test_assert_unlocked_raises_when_locked(tmp_path):
    cfg = make_config(tmp_path)
    lock_profile(cfg, "local")
    with pytest.raises(LockError, match="locked"):
        assert_unlocked(cfg, "local")


def test_locks_persisted_to_disk(tmp_path):
    cfg = make_config(tmp_path)
    lock_profile(cfg, "staging")
    locks_file = tmp_path / "locks.json"
    assert locks_file.exists()
    data = json.loads(locks_file.read_text())
    assert "staging" in data
