"""Trim whitespace and normalize values across a profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.config import Config


class TrimError(Exception):
    """Raised when trimming fails."""


@dataclass
class TrimResult:
    trimmed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_trimmed(self) -> int:
        return len(self.trimmed)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)


def trim_profile(
    config: Config,
    profile: str,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> TrimResult:
    """Trim leading/trailing whitespace from values in a profile.

    Args:
        config: The active Config instance.
        profile: Name of the profile to trim.
        keys: Optional list of specific keys to trim. Trims all if None.
        dry_run: If True, report changes without saving.

    Returns:
        TrimResult with lists of trimmed and skipped keys.

    Raises:
        TrimError: If the profile does not exist.
    """
    data = config.get_profile(profile)
    if data is None:
        raise TrimError(f"Profile '{profile}' does not exist.")

    result = TrimResult()
    target_keys = keys if keys is not None else list(data.keys())

    updated = dict(data)
    for key in target_keys:
        if key not in data:
            result.skipped.append(key)
            continue
        original = data[key]
        trimmed = original.strip()
        if trimmed != original:
            updated[key] = trimmed
            result.trimmed.append(key)
        else:
            result.skipped.append(key)

    if not dry_run and result.trimmed:
        config.set_profile(profile, updated)
        config.save()

    return result
