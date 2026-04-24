"""Profile locking — prevent accidental writes to protected profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class LockError(Exception):
    """Raised when a lock operation fails."""


def _lock_path(config) -> Path:
    return Path(config.path).parent / "locks.json"


def _load_locks(config) -> List[str]:
    p = _lock_path(config)
    if not p.exists():
        return []
    return json.loads(p.read_text())


def _save_locks(config, locks: List[str]) -> None:
    _lock_path(config).write_text(json.dumps(sorted(set(locks)), indent=2))


def lock_profile(config, profile: str) -> bool:
    """Lock *profile*. Returns True if newly locked, False if already locked."""
    envs = config.config.get("envs", {})
    if profile not in envs:
        raise LockError(f"Profile '{profile}' does not exist.")
    locks = _load_locks(config)
    if profile in locks:
        return False
    locks.append(profile)
    _save_locks(config, locks)
    return True


def unlock_profile(config, profile: str) -> bool:
    """Unlock *profile*. Returns True if unlocked, False if it was not locked."""
    locks = _load_locks(config)
    if profile not in locks:
        return False
    locks.remove(profile)
    _save_locks(config, locks)
    return True


def is_locked(config, profile: str) -> bool:
    """Return True if *profile* is currently locked."""
    return profile in _load_locks(config)


def list_locked(config) -> List[str]:
    """Return a sorted list of all locked profile names."""
    return sorted(_load_locks(config))


def assert_unlocked(config, profile: str) -> None:
    """Raise LockError if *profile* is locked."""
    if is_locked(config, profile):
        raise LockError(
            f"Profile '{profile}' is locked. Run `envctl lock remove {profile}` to unlock it."
        )
