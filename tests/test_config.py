"""Tests for envctl config module."""

import json
import pytest
from pathlib import Path
from envctl.config import Config


@pytest.fixture
def tmp_config(tmp_path):
    config_file = tmp_path / "config.json"
    return Config(config_path=config_file)


def test_default_active_env(tmp_config):
    assert tmp_config.get_active_env() == "local"


def test_set_active_env(tmp_config):
    tmp_config.set_active_env("staging")
    assert tmp_config.get_active_env() == "staging"


def test_set_invalid_env(tmp_config):
    with pytest.raises(ValueError, match="Invalid environment"):
        tmp_config.set_active_env("dev")


def test_set_and_get_profile(tmp_config):
    tmp_config.set_profile("local", {"DB_HOST": "localhost", "PORT": "5432"})
    profile = tmp_config.get_profile("local")
    assert profile["DB_HOST"] == "localhost"
    assert profile["PORT"] == "5432"


def test_get_missing_profile_returns_empty(tmp_config):
    assert tmp_config.get_profile("production") == {}


def test_list_envs(tmp_config):
    tmp_config.set_profile("local", {"KEY": "val"})
    tmp_config.set_profile("staging", {"KEY": "val2"})
    envs = tmp_config.list_envs()
    assert "local" in envs
    assert "staging" in envs


def test_persistence(tmp_path):
    config_file = tmp_path / "config.json"
    c1 = Config(config_path=config_file)
    c1.set_profile("production", {"API_KEY": "secret"})
    c1.set_active_env("production")

    c2 = Config(config_path=config_file)
    assert c2.get_active_env() == "production"
    assert c2.get_profile("production")["API_KEY"] == "secret"
