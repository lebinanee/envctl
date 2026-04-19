"""Tests for envctl.pin module."""

import pytest
from unittest.mock import MagicMock
from envctl.pin import PinError, pin_key, unpin_key, list_pins, is_pinned, PINS_KEY


def make_config(profiles: dict):
    config = MagicMock()
    store = {k: dict(v) for k, v in profiles.items()}

    def get_profile(name):
        return store.get(name)

    def set_profile(name, data):
        store[name] = data

    config.get_profile.side_effect = get_profile
    config.set_profile.side_effect = set_profile
    config.save = MagicMock()
    return config


def test_pin_key_success():
    config = make_config({"local": {"API_KEY": "abc"}})
    result = pin_key(config, "local", "API_KEY")
    assert result is True
    assert is_pinned(config, "local", "API_KEY")


def test_pin_key_already_pinned():
    config = make_config({"local": {"API_KEY": "abc", PINS_KEY: ["API_KEY"]}})
    result = pin_key(config, "local", "API_KEY")
    assert result is False


def test_pin_missing_profile_raises():
    config = make_config({})
    with pytest.raises(PinError, match="Profile"):
        pin_key(config, "ghost", "KEY")


def test_pin_missing_key_raises():
    config = make_config({"local": {}})
    with pytest.raises(PinError, match="Key"):
        pin_key(config, "local", "MISSING")


def test_unpin_key_success():
    config = make_config({"local": {"API_KEY": "abc", PINS_KEY: ["API_KEY"]}})
    result = unpin_key(config, "local", "API_KEY")
    assert result is True
    assert not is_pinned(config, "local", "API_KEY")


def test_unpin_key_not_pinned():
    config = make_config({"local": {"API_KEY": "abc"}})
    result = unpin_key(config, "local", "API_KEY")
    assert result is False


def test_list_pins_empty():
    config = make_config({"local": {"X": "1"}})
    assert list_pins(config, "local") == []


def test_list_pins_returns_all():
    config = make_config({"local": {"A": "1", "B": "2", PINS_KEY: ["A", "B"]}})
    pins = list_pins(config, "local")
    assert set(pins) == {"A", "B"}


def test_list_pins_missing_profile_raises():
    config = make_config({})
    with pytest.raises(PinError):
        list_pins(config, "nope")


def test_save_called_on_pin():
    config = make_config({"local": {"K": "v"}})
    pin_key(config, "local", "K")
    config.save.assert_called_once()
