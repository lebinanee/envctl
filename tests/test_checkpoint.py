"""Tests for envctl.checkpoint."""
from __future__ import annotations

import json
import pytest

from envctl.checkpoint import (
    CheckpointError,
    create_checkpoint,
    delete_checkpoint,
    list_checkpoints,
    restore_checkpoint,
)


class FakeConfig:
    def __init__(self, tmp_path):
        self.path = str(tmp_path / "envctl.json")
        self._profiles: dict = {}

    def get_profile(self, profile):
        return self._profiles.get(profile)

    def set_profile(self, profile, vars_):
        self._profiles[profile] = dict(vars_)

    def save(self):
        pass


def make_config(tmp_path, profiles=None):
    cfg = FakeConfig(tmp_path)
    for name, vars_ in (profiles or {}).items():
        cfg.set_profile(name, vars_)
    return cfg


def test_create_checkpoint_stores_entry(tmp_path):
    cfg = make_config(tmp_path, {"local": {"KEY": "val"}})
    entry = create_checkpoint(cfg, "local", "before-deploy")
    assert entry["name"] == "before-deploy"
    assert entry["profile"] == "local"
    assert entry["vars"] == {"KEY": "val"}
    assert entry["timestamp"] > 0


def test_create_checkpoint_with_note(tmp_path):
    cfg = make_config(tmp_path, {"local": {"A": "1"}})
    entry = create_checkpoint(cfg, "local", "cp1", note="pre-release")
    assert entry["note"] == "pre-release"


def test_create_checkpoint_missing_profile_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(CheckpointError, match="not found"):
        create_checkpoint(cfg, "staging", "cp1")


def test_create_checkpoint_empty_name_raises(tmp_path):
    cfg = make_config(tmp_path, {"local": {"X": "1"}})
    with pytest.raises(CheckpointError, match="name must not be empty"):
        create_checkpoint(cfg, "local", "   ")


def test_list_checkpoints_all(tmp_path):
    cfg = make_config(tmp_path, {"local": {"A": "1"}, "prod": {"B": "2"}})
    create_checkpoint(cfg, "local", "cp1")
    create_checkpoint(cfg, "prod", "cp2")
    entries = list_checkpoints(cfg)
    assert len(entries) == 2


def test_list_checkpoints_filtered(tmp_path):
    cfg = make_config(tmp_path, {"local": {"A": "1"}, "prod": {"B": "2"}})
    create_checkpoint(cfg, "local", "cp1")
    create_checkpoint(cfg, "prod", "cp2")
    entries = list_checkpoints(cfg, profile="local")
    assert all(e["profile"] == "local" for e in entries)
    assert len(entries) == 1


def test_restore_checkpoint(tmp_path):
    cfg = make_config(tmp_path, {"local": {"KEY": "original"}})
    create_checkpoint(cfg, "local", "snap1")
    cfg.set_profile("local", {"KEY": "modified", "NEW": "extra"})
    restored = restore_checkpoint(cfg, "local", "snap1")
    assert restored == {"KEY": "original"}
    assert cfg.get_profile("local") == {"KEY": "original"}


def test_restore_missing_checkpoint_raises(tmp_path):
    cfg = make_config(tmp_path, {"local": {"A": "1"}})
    with pytest.raises(CheckpointError, match="not found"):
        restore_checkpoint(cfg, "local", "ghost")


def test_delete_checkpoint_success(tmp_path):
    cfg = make_config(tmp_path, {"local": {"A": "1"}})
    create_checkpoint(cfg, "local", "cp1")
    result = delete_checkpoint(cfg, "local", "cp1")
    assert result is True
    assert list_checkpoints(cfg) == []


def test_delete_checkpoint_missing_returns_false(tmp_path):
    cfg = make_config(tmp_path, {"local": {"A": "1"}})
    result = delete_checkpoint(cfg, "local", "nonexistent")
    assert result is False
