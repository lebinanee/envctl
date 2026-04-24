"""Key rotation: rename a key across one or all profiles, preserving values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.config import Config
from envctl.validate import validate_key


class RotateError(Exception):
    """Raised when key rotation fails."""


@dataclass
class RotateResult:
    old_key: str
    new_key: str
    updated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_updated(self) -> int:
        return len(self.updated)


def rotate_key(
    config: Config,
    old_key: str,
    new_key: str,
    profile: Optional[str] = None,
    overwrite: bool = False,
) -> RotateResult:
    """Rename *old_key* to *new_key* in one profile or all profiles.

    Parameters
    ----------
    config:    Loaded Config instance.
    old_key:   Existing key name to rotate away from.
    new_key:   Replacement key name.
    profile:   If given, only rotate within that profile.
    overwrite: If True, overwrite *new_key* when it already exists.

    Returns a RotateResult describing what changed.
    """
    validate_key(new_key)

    result = RotateResult(old_key=old_key, new_key=new_key)

    profiles = [profile] if profile else list(config.data.get("profiles", {}).keys())

    for prof in profiles:
        vars_ = config.get_profile(prof)
        if vars_ is None:
            raise RotateError(f"Profile '{prof}' does not exist.")

        if old_key not in vars_:
            result.skipped.append(prof)
            continue

        if new_key in vars_ and not overwrite:
            result.skipped.append(prof)
            continue

        value = vars_.pop(old_key)
        vars_[new_key] = value
        config.set_profile(prof, vars_)
        result.updated.append(prof)

    if result.updated:
        config.save()

    return result
