"""Unit tests for envctl.patch."""

from __future__ import annotations

import pytest

from envctl.patch import patch_profile, PatchError, PatchResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeConfig:
    def __init__(self, profiles: dict):
        self._profiles = {k: dict(v) for k, v in profiles.items()}
        self.saved = False

    def get_profile(self, name: str):
        return self._profiles.get(name)

    def set_profile(self, name: str, data: dict):
        self._profiles[name] = dict(data)

    def save(self):
        self.saved = True


def make_config(**profiles):
    return FakeConfig(profiles)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_patch_applies_new_key():
    cfg = make_config(local={"FOO": "bar"})
    result = patch_profile(cfg, "local", {"BAZ": "qux"})
    assert "BAZ" in result.applied
    assert cfg._profiles["local"]["BAZ"] == "qux"
    assert cfg.saved


def test_patch_overwrites_existing_by_default():
    cfg = make_config(local={"FOO": "old"})
    result = patch_profile(cfg, "local", {"FOO": "new"})
    assert result.applied["FOO"] == "new"
    assert cfg._profiles["local"]["FOO"] == "new"


def test_patch_skips_existing_when_no_overwrite():
    cfg = make_config(local={"FOO": "old"})
    result = patch_profile(cfg, "local", {"FOO": "new"}, overwrite=False)
    assert "FOO" in result.skipped
    assert cfg._profiles["local"]["FOO"] == "old"


def test_patch_missing_profile_raises():
    cfg = make_config()
    with pytest.raises(PatchError, match="does not exist"):
        patch_profile(cfg, "ghost", {"X": "1"})


def test_patch_dry_run_does_not_save():
    cfg = make_config(local={"A": "1"})
    result = patch_profile(cfg, "local", {"B": "2"}, dry_run=True)
    assert result.total_applied == 1
    assert not cfg.saved
    assert "B" not in cfg._profiles["local"]


def test_patch_keys_filter():
    cfg = make_config(local={})
    result = patch_profile(cfg, "local", {"X": "1", "Y": "2"}, keys=["X"])
    assert "X" in result.applied
    assert "Y" not in result.applied
    assert "Y" not in cfg._profiles["local"]


def test_patch_invalid_key_recorded_as_error():
    cfg = make_config(local={})
    result = patch_profile(cfg, "local", {"bad key": "val"})
    assert result.errors
    assert result.total_applied == 0


def test_patch_multiple_pairs():
    cfg = make_config(prod={})
    patch = {"HOST": "localhost", "PORT": "5432", "DB": "mydb"}
    result = patch_profile(cfg, "prod", patch)
    assert result.total_applied == 3
    assert cfg._profiles["prod"] == patch
