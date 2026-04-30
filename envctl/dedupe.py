"""Detect and remove duplicate values across keys within a profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class DedupeError(Exception):
    """Raised when deduplication fails."""


@dataclass
class DedupeResult:
    removed: List[str] = field(default_factory=list)
    kept: Dict[str, str] = field(default_factory=dict)  # value -> canonical key
    skipped: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed)


def dedupe_profile(
    config,
    profile: str,
    *,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> DedupeResult:
    """Remove keys whose values are duplicates of an earlier key in *profile*.

    When *keys* is given only those keys are considered; all others are left
    untouched.  The first key encountered for a given value is kept; subsequent
    ones are removed (or reported when *dry_run* is True).
    """
    vars_ = config.get_profile(profile)
    if vars_ is None:
        raise DedupeError(f"Profile '{profile}' not found.")

    candidates = {k: v for k, v in vars_.items() if keys is None or k in keys}
    result = DedupeResult()

    seen: Dict[str, str] = {}  # value -> first key
    to_remove: List[str] = []

    for key, value in candidates.items():
        if value in seen:
            to_remove.append(key)
            result.removed.append(key)
        else:
            seen[value] = key
            result.kept[value] = key

    if keys is not None:
        unchecked = [k for k in vars_ if k not in candidates]
        result.skipped.extend(unchecked)

    if not dry_run and to_remove:
        updated = {k: v for k, v in vars_.items() if k not in to_remove}
        config.set_profile(profile, updated)
        config.save()

    return result
