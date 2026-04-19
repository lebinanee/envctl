"""Tests for envctl.clone."""
import pytest
from unittest.mock import MagicMock
from envctl.clone import clone_profile, CloneError


def make_config(profiles: dict) -> MagicMock:
    cfg = MagicMock()
    store: dict = {k: dict(v) for k, v in profiles.items()}

    def _get_profile(name):
        return store.get(name)

    def _set_profile(name, data):
        store[name] = dict(data)

    cfg.get_profile.side_effect = _get_profile
    cfg.set_profile.side_effect = _set_profile
    cfg.save = MagicMock()
    cfg._store = store
    return cfg


def test_clone_copies_all_keys():
    cfg = make_config({"local": {"DB_URL": "sqlite", "DEBUG": "true"}})
    count = clone_profile(cfg, "local", "staging")
    assert count == 2
    assert cfg._store["staging"] == {"DB_URL": "sqlite", "DEBUG": "true"}
    cfg.save.assert_called_once()


def test_clone_missing_src_raises():
    cfg = make_config({})
    with pytest.raises(CloneError, match="Source profile 'local' does not exist"):
        clone_profile(cfg, "local", "staging")


def test_clone_existing_dest_raises_without_overwrite():
    cfg = make_config({"local": {"A": "1"}, "staging": {"B": "2"}})
    with pytest.raises(CloneError, match="already exists"):
        clone_profile(cfg, "local", "staging")


def test_clone_existing_dest_overwrite():
    cfg = make_config({"local": {"A": "1"}, "staging": {"B": "2"}})
    count = clone_profile(cfg, "local", "staging", overwrite=True)
    assert count == 1
    assert cfg._store["staging"] == {"A": "1"}


def test_clone_empty_profile():
    cfg = make_config({"local": {}})
    count = clone_profile(cfg, "local", "staging")
    assert count == 0
    assert cfg._store["staging"] == {}


def test_clone_does_not_mutate_src():
    cfg = make_config({"local": {"KEY": "val"}})
    clone_profile(cfg, "local", "staging")
    cfg._store["staging"]["KEY"] = "changed"
    assert cfg._store["local"]["KEY"] == "val"
