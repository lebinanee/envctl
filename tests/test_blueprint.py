"""Tests for envctl/blueprint.py"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envctl.blueprint import (
    Blueprint,
    BlueprintError,
    apply_blueprint,
    delete_blueprint,
    get_blueprint,
    list_blueprints,
    save_blueprint,
)


class FakeConfig:
    def __init__(self, tmp_path: Path):
        self.path = str(tmp_path / "envctl.json")
        self._profiles: dict = {}

    def get_profile(self, name: str):
        return dict(self._profiles.get(name, {}))

    def set_profile(self, name: str, data: dict):
        self._profiles[name] = dict(data)

    def save(self):
        pass


def make_config(tmp_path):
    return FakeConfig(tmp_path)


def test_save_and_get_blueprint(tmp_path):
    cfg = make_config(tmp_path)
    bp = save_blueprint(cfg, "base", {"HOST": "localhost", "PORT": "5432"})
    assert bp.name == "base"
    assert bp.keys == {"HOST": "localhost", "PORT": "5432"}
    fetched = get_blueprint(cfg, "base")
    assert fetched.keys == bp.keys


def test_save_blueprint_with_description(tmp_path):
    cfg = make_config(tmp_path)
    bp = save_blueprint(cfg, "db", {"DB_URL": "postgres://"}, description="DB defaults")
    assert bp.description == "DB defaults"


def test_save_blueprint_invalid_name_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(BlueprintError):
        save_blueprint(cfg, "bad-name!", {"KEY": "val"})


def test_get_missing_blueprint_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(BlueprintError):
        get_blueprint(cfg, "nonexistent")


def test_list_blueprints_sorted(tmp_path):
    cfg = make_config(tmp_path)
    save_blueprint(cfg, "zebra", {"Z": "1"})
    save_blueprint(cfg, "alpha", {"A": "2"})
    names = [b.name for b in list_blueprints(cfg)]
    assert names == ["alpha", "zebra"]


def test_delete_blueprint(tmp_path):
    cfg = make_config(tmp_path)
    save_blueprint(cfg, "temp", {"K": "v"})
    assert delete_blueprint(cfg, "temp") is True
    with pytest.raises(BlueprintError):
        get_blueprint(cfg, "temp")


def test_delete_missing_blueprint_returns_false(tmp_path):
    cfg = make_config(tmp_path)
    assert delete_blueprint(cfg, "ghost") is False


def test_apply_blueprint_writes_keys(tmp_path):
    cfg = make_config(tmp_path)
    save_blueprint(cfg, "defaults", {"HOST": "localhost", "PORT": "8080"})
    applied = apply_blueprint(cfg, "defaults", "local")
    assert applied == {"HOST": "localhost", "PORT": "8080"}
    assert cfg.get_profile("local")["HOST"] == "localhost"


def test_apply_blueprint_skips_existing_without_overwrite(tmp_path):
    cfg = make_config(tmp_path)
    cfg.set_profile("local", {"HOST": "prod.host"})
    save_blueprint(cfg, "defaults", {"HOST": "localhost", "PORT": "8080"})
    applied = apply_blueprint(cfg, "defaults", "local")
    assert "HOST" not in applied
    assert cfg.get_profile("local")["HOST"] == "prod.host"


def test_apply_blueprint_overwrites_when_flag_set(tmp_path):
    cfg = make_config(tmp_path)
    cfg.set_profile("local", {"HOST": "prod.host"})
    save_blueprint(cfg, "defaults", {"HOST": "localhost"})
    applied = apply_blueprint(cfg, "defaults", "local", overwrite=True)
    assert applied == {"HOST": "localhost"}
    assert cfg.get_profile("local")["HOST"] == "localhost"
