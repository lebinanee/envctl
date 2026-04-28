"""Tests for envctl.freeze module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envctl.freeze import (
    FreezeError,
    freeze_profile,
    unfreeze_profile,
    is_frozen,
    list_frozen,
    assert_not_frozen,
    _freeze_path,
)


def make_config(tmp_path, profiles=None):
    config = MagicMock()
    config.config_dir = str(tmp_path)
    env_profiles = profiles if profiles is not None else {"local": {"A": "1"}, "staging": {}}
    config.get_active_env.return_value = "default"
    config.get.return_value = env_profiles
    return config


def test_freeze_profile_success(tmp_path):
    config = make_config(tmp_path)
    result = freeze_profile(config, "local")
    assert result is True
    assert is_frozen(config, "local")


def test_freeze_profile_already_frozen(tmp_path):
    config = make_config(tmp_path)
    freeze_profile(config, "local")
    result = freeze_profile(config, "local")
    assert result is False


def test_freeze_missing_profile_raises(tmp_path):
    config = make_config(tmp_path)
    with pytest.raises(FreezeError, match="does not exist"):
        freeze_profile(config, "nonexistent")


def test_unfreeze_profile_success(tmp_path):
    config = make_config(tmp_path)
    freeze_profile(config, "local")
    result = unfreeze_profile(config, "local")
    assert result is True
    assert not is_frozen(config, "local")


def test_unfreeze_profile_not_frozen(tmp_path):
    config = make_config(tmp_path)
    result = unfreeze_profile(config, "local")
    assert result is False


def test_list_frozen_empty(tmp_path):
    config = make_config(tmp_path)
    assert list_frozen(config) == []


def test_list_frozen_multiple(tmp_path):
    config = make_config(tmp_path)
    freeze_profile(config, "local")
    freeze_profile(config, "staging")
    assert list_frozen(config) == ["local", "staging"]


def test_assert_not_frozen_raises_when_frozen(tmp_path):
    config = make_config(tmp_path)
    freeze_profile(config, "local")
    with pytest.raises(FreezeError, match="frozen"):
        assert_not_frozen(config, "local")


def test_assert_not_frozen_passes_when_not_frozen(tmp_path):
    config = make_config(tmp_path)
    assert_not_frozen(config, "local")  # should not raise


def test_freeze_file_is_sorted_json(tmp_path):
    config = make_config(tmp_path)
    freeze_profile(config, "staging")
    freeze_profile(config, "local")
    data = json.loads(_freeze_path(config).read_text())
    assert data == ["local", "staging"]
