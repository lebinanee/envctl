"""Tests for envctl.annotate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envctl.annotate import AnnotateError, get_annotation, list_annotations, remove_annotation, set_annotation


class FakeConfig:
    def __init__(self, tmp_path: Path):
        self.path = str(tmp_path / "config.json")
        self._profiles: dict = {}

    def get_profile(self, profile: str):
        return self._profiles.get(profile)


def make_config(tmp_path: Path, profiles: dict | None = None) -> FakeConfig:
    cfg = FakeConfig(tmp_path)
    if profiles:
        cfg._profiles = profiles
    return cfg


def test_set_annotation_success(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"API_KEY": "abc"}})
    set_annotation(cfg, "dev", "API_KEY", "Main API key")
    note = get_annotation(cfg, "dev", "API_KEY")
    assert note == "Main API key"


def test_set_annotation_missing_profile_raises(tmp_path):
    cfg = make_config(tmp_path, {})
    with pytest.raises(AnnotateError, match="Profile"):
        set_annotation(cfg, "ghost", "KEY", "note")


def test_set_annotation_missing_key_raises(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"OTHER": "x"}})
    with pytest.raises(AnnotateError, match="Key"):
        set_annotation(cfg, "dev", "MISSING", "note")


def test_get_annotation_returns_none_when_absent(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"X": "1"}})
    result = get_annotation(cfg, "dev", "X")
    assert result is None


def test_set_annotation_overwrites_existing(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"DB_URL": "postgres://"}})
    set_annotation(cfg, "dev", "DB_URL", "first")
    set_annotation(cfg, "dev", "DB_URL", "updated")
    assert get_annotation(cfg, "dev", "DB_URL") == "updated"


def test_remove_annotation_returns_true(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"TOKEN": "t"}})
    set_annotation(cfg, "dev", "TOKEN", "my token")
    result = remove_annotation(cfg, "dev", "TOKEN")
    assert result is True
    assert get_annotation(cfg, "dev", "TOKEN") is None


def test_remove_annotation_returns_false_when_absent(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"KEY": "v"}})
    result = remove_annotation(cfg, "dev", "KEY")
    assert result is False


def test_list_annotations_returns_all(tmp_path):
    cfg = make_config(tmp_path, {"dev": {"A": "1", "B": "2"}})
    set_annotation(cfg, "dev", "A", "note-a")
    set_annotation(cfg, "dev", "B", "note-b")
    result = list_annotations(cfg, "dev")
    assert result == {"A": "note-a", "B": "note-b"}


def test_list_annotations_empty_profile(tmp_path):
    cfg = make_config(tmp_path, {"dev": {}})
    result = list_annotations(cfg, "dev")
    assert result == {}


def test_annotations_persisted_to_disk(tmp_path):
    cfg = make_config(tmp_path, {"prod": {"SECRET": "s"}})
    set_annotation(cfg, "prod", "SECRET", "production secret")
    ann_file = Path(cfg.path).parent / ".envctl" / "annotations.json"
    assert ann_file.exists()
    data = json.loads(ann_file.read_text())
    assert data["prod"]["SECRET"] == "production secret"
