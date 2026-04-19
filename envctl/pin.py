"""Pin/unpin specific keys to prevent accidental overwrites during sync."""

from __future__ import annotations
from typing import List
from envctl.config import Config

PINS_KEY = "__pins__"


class PinError(Exception):
    pass


def _get_pins(config: Config, profile: str) -> List[str]:
    data = config.get_profile(profile) or {}
    return list(data.get(PINS_KEY, []))


def _save_pins(config: Config, profile: str, pins: List[str]) -> None:
    data = config.get_profile(profile) or {}
    data[PINS_KEY] = pins
    config.set_profile(profile, data)
    config.save()


def pin_key(config: Config, profile: str, key: str) -> bool:
    """Pin a key in the given profile. Returns True if newly pinned."""
    prof = config.get_profile(profile)
    if prof is None:
        raise PinError(f"Profile '{profile}' does not exist.")
    if key not in prof:
        raise PinError(f"Key '{key}' not found in profile '{profile}'.")
    pins = _get_pins(config, profile)
    if key in pins:
        return False
    pins.append(key)
    _save_pins(config, profile, pins)
    return True


def unpin_key(config: Config, profile: str, key: str) -> bool:
    """Unpin a key. Returns True if it was pinned."""
    pins = _get_pins(config, profile)
    if key not in pins:
        return False
    pins.remove(key)
    _save_pins(config, profile, pins)
    return True


def list_pins(config: Config, profile: str) -> List[str]:
    """Return all pinned keys for a profile."""
    if config.get_profile(profile) is None:
        raise PinError(f"Profile '{profile}' does not exist.")
    return _get_pins(config, profile)


def is_pinned(config: Config, profile: str, key: str) -> bool:
    return key in _get_pins(config, profile)
