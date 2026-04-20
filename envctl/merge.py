"""Merge variables from one profile into another with conflict resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class MergeError(Exception):
    """Raised when a merge operation fails."""


@dataclass
class MergeResult:
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.updated)


def merge_profiles(
    config,
    src: str,
    dst: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> MergeResult:
    """Merge variables from *src* profile into *dst* profile.

    Args:
        config: Config instance.
        src: Source profile name.
        dst: Destination profile name.
        keys: Optional list of specific keys to merge; merges all if None.
        overwrite: If True, overwrite existing keys in dst.
        dry_run: If True, compute result without persisting changes.

    Returns:
        MergeResult describing what was (or would be) changed.
    """
    data = config._load()
    profiles = data.get("profiles", {})

    if src not in profiles:
        raise MergeError(f"Source profile '{src}' does not exist.")
    if dst not in profiles:
        raise MergeError(f"Destination profile '{dst}' does not exist.")

    src_vars: Dict[str, str] = profiles[src].get("vars", {})
    dst_vars: Dict[str, str] = profiles[dst].get("vars", {})

    candidates = {k: v for k, v in src_vars.items() if keys is None or k in keys}

    if keys:
        missing = set(keys) - set(src_vars)
        if missing:
            raise MergeError(
                f"Keys not found in source profile '{src}': {', '.join(sorted(missing))}"
            )

    result = MergeResult()

    for key, value in candidates.items():
        if key in dst_vars:
            if dst_vars[key] == value:
                result.skipped.append(key)
            elif overwrite:
                result.updated.append(key)
                if not dry_run:
                    dst_vars[key] = value
            else:
                result.conflicts.append(key)
        else:
            result.added.append(key)
            if not dry_run:
                dst_vars[key] = value

    if not dry_run and result.total_changes > 0:
        profiles[dst]["vars"] = dst_vars
        config.save(data)

    return result
