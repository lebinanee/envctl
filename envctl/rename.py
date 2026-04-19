"""Rename a key across one or all profiles."""

from __future__ import annotations
from typing import Optional
from envctl.config import Config
from envctl.validate import validate_key


class RenameError(Exception):
    pass


def rename_key(
    config: Config,
    old_key: str,
    new_key: str,
    profile: Optional[str] = None,
) -> dict[str, bool]:
    """Rename *old_key* to *new_key* in one or all profiles.

    Returns a mapping of profile -> whether the rename happened.

    Raises:
        RenameError: If *new_key* already exists in a target profile, or if
            a specific *profile* is given but does not exist in the config.
    """
    validate_key(old_key)
    validate_key(new_key)

    all_profiles: dict = config.data.get("profiles", {})

    if profile:
        if profile not in all_profiles:
            raise RenameError(f"Profile '{profile}' does not exist")
        profiles = [profile]
    else:
        profiles = list(all_profiles.keys())

    results: dict[str, bool] = {}

    for prof in profiles:
        env = all_profiles.get(prof, {})
        if old_key not in env:
            results[prof] = False
            continue
        if new_key in env:
            raise RenameError(
                f"Key '{new_key}' already exists in profile '{prof}'"
            )
        env[new_key] = env.pop(old_key)
        results[prof] = True

    config.save()
    return results
