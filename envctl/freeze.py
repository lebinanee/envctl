"""Freeze/unfreeze profiles to prevent any modifications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


class FreezeError(Exception):
    """Raised when a freeze/unfreeze operation fails."""


def _freeze_path(config) -> Path:
    return Path(config.config_dir) / "freeze.json"


def _load_frozen(config) -> List[str]:
    path = _freeze_path(config)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_frozen(config, frozen: List[str]) -> None:
    path = _freeze_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(set(frozen)), indent=2))


def freeze_profile(config, profile: str) -> bool:
    """Freeze a profile. Returns True if newly frozen, False if already frozen."""
    env = config.get_active_env()
    available = config.get("profiles", env, default={}).keys()
    if profile not in available:
        raise FreezeError(f"Profile '{profile}' does not exist.")
    frozen = _load_frozen(config)
    if profile in frozen:
        return False
    frozen.append(profile)
    _save_frozen(config, frozen)
    return True


def unfreeze_profile(config, profile: str) -> bool:
    """Unfreeze a profile. Returns True if unfrozen, False if was not frozen."""
    frozen = _load_frozen(config)
    if profile not in frozen:
        return False
    frozen = [p for p in frozen if p != profile]
    _save_frozen(config, frozen)
    return True


def is_frozen(config, profile: str) -> bool:
    """Return True if the profile is currently frozen."""
    return profile in _load_frozen(config)


def list_frozen(config) -> List[str]:
    """Return a sorted list of all frozen profiles."""
    return sorted(_load_frozen(config))


def assert_not_frozen(config, profile: str) -> None:
    """Raise FreezeError if the profile is frozen."""
    if is_frozen(config, profile):
        raise FreezeError(
            f"Profile '{profile}' is frozen and cannot be modified. "
            "Run 'envctl freeze unfreeze {profile}' to allow changes."
        )
