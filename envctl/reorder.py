"""Reorder keys within a profile by sorting or custom ordering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class ReorderError(Exception):
    """Raised when a reorder operation fails."""


@dataclass
class ReorderResult:
    profile: str
    original_order: List[str] = field(default_factory=list)
    new_order: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original_order != self.new_order


def reorder_profile(
    config,
    profile: str,
    *,
    keys: Optional[List[str]] = None,
    alphabetical: bool = False,
    reverse: bool = False,
) -> ReorderResult:
    """Reorder keys in *profile*.

    If *keys* is provided the profile is reordered to match that sequence
    (unknown keys are appended at the end in their original relative order).
    If *alphabetical* is True the keys are sorted lexicographically.
    *reverse* inverts whichever ordering is applied.

    Raises :class:`ReorderError` when the profile does not exist.
    """
    data = config.get_profile(profile)
    if data is None:
        raise ReorderError(f"Profile '{profile}' not found.")

    original = list(data.keys())

    if keys is not None:
        known = [k for k in keys if k in data]
        rest = [k for k in original if k not in known]
        ordered = known + rest
    elif alphabetical:
        ordered = sorted(original)
    else:
        ordered = list(original)

    if reverse:
        ordered = list(reversed(ordered))

    new_data = {k: data[k] for k in ordered}
    config.get_profile.__self__ if hasattr(config.get_profile, "__self__") else None

    # Write back via set_profile / save pattern used across the project
    raw = config._data  # type: ignore[attr-defined]
    raw.setdefault("profiles", {})[profile] = new_data
    config.save()

    return ReorderResult(profile=profile, original_order=original, new_order=ordered)
