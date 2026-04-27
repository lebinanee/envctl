"""protect.py — Mark environment variable keys as protected (read-only).

Protected keys cannot be overwritten or deleted without explicit unprotection.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional


class ProtectError(Exception):
    """Raised when a protection operation fails."""


def _protect_path(config) -> Path:
    return Path(config.path).parent / ".envctl_protected.json"


def _load_protected(config) -> dict:
    p = _protect_path(config)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_protected(config, data: dict) -> None:
    _protect_path(config).write_text(json.dumps(data, indent=2))


def protect_key(config, profile: str, key: str) -> bool:
    """Mark *key* in *profile* as protected. Returns True if newly protected."""
    env = config.get_profile(profile)
    if env is None:
        raise ProtectError(f"Profile '{profile}' does not exist.")
    if key not in env:
        raise ProtectError(f"Key '{key}' not found in profile '{profile}'.")
    data = _load_protected(config)
    keys: List[str] = data.get(profile, [])
    if key in keys:
        return False
    keys.append(key)
    data[profile] = keys
    _save_protected(config, data)
    return True


def unprotect_key(config, profile: str, key: str) -> bool:
    """Remove protection from *key* in *profile*. Returns True if removed."""
    data = _load_protected(config)
    keys: List[str] = data.get(profile, [])
    if key not in keys:
        return False
    keys.remove(key)
    data[profile] = keys
    _save_protected(config, data)
    return True


def is_protected(config, profile: str, key: str) -> bool:
    """Return True if *key* in *profile* is protected."""
    data = _load_protected(config)
    return key in data.get(profile, [])


def list_protected(config, profile: str) -> List[str]:
    """Return all protected keys for *profile*."""
    data = _load_protected(config)
    return list(data.get(profile, []))


def assert_not_protected(config, profile: str, key: str, operation: str = "modify") -> None:
    """Raise ProtectError if *key* is protected."""
    if is_protected(config, profile, key):
        raise ProtectError(
            f"Key '{key}' in profile '{profile}' is protected and cannot be {operation}d."
        )
