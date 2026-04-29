"""Prune unused or empty keys from environment profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class PruneError(Exception):
    """Raised when pruning fails."""


@dataclass
class PruneResult:
    removed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)


def prune_profile(
    config,
    profile: str,
    *,
    remove_empty: bool = True,
    remove_whitespace_only: bool = True,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> PruneResult:
    """Remove empty or whitespace-only keys from a profile.

    Args:
        config: Config instance.
        profile: Name of the profile to prune.
        remove_empty: Remove keys with empty string values.
        remove_whitespace_only: Remove keys whose values are only whitespace.
        keys: If provided, only consider these keys for pruning.
        dry_run: If True, do not persist changes.

    Returns:
        PruneResult describing what was removed and skipped.
    """
    vars_ = config.get_profile(profile)
    if vars_ is None:
        raise PruneError(f"Profile '{profile}' does not exist.")

    result = PruneResult()
    candidates = keys if keys is not None else list(vars_.keys())
    updated = dict(vars_)

    for key in candidates:
        if key not in updated:
            result.skipped.append(key)
            continue

        value = updated[key]
        should_remove = (remove_empty and value == "") or (
            remove_whitespace_only and value != "" and value.strip() == ""
        )

        if should_remove:
            result.removed.append(key)
            if not dry_run:
                del updated[key]
        else:
            result.skipped.append(key)

    if not dry_run and result.removed:
        config.set_profile(profile, updated)
        config.save()

    return result
