"""Profile inheritance: merge a base profile's vars into a child profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class InheritError(Exception):
    """Raised when profile inheritance fails."""


@dataclass
class InheritResult:
    inherited: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.inherited) + len(self.overwritten)


def inherit_profile(
    config,
    base: str,
    child: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> InheritResult:
    """Copy variables from *base* into *child*, respecting existing keys.

    Args:
        config:    A Config instance.
        base:      Name of the source (parent) profile.
        child:     Name of the destination (child) profile.
        keys:      Optional allowlist of keys to inherit. None means all.
        overwrite: If True, overwrite keys that already exist in *child*.
        dry_run:   If True, compute the result but do not persist changes.

    Returns:
        An InheritResult describing what was inherited, skipped, or overwritten.
    """
    base_vars = config.get_profile(base)
    if base_vars is None:
        raise InheritError(f"Base profile '{base}' does not exist.")

    child_vars = config.get_profile(child)
    if child_vars is None:
        raise InheritError(f"Child profile '{child}' does not exist.")

    result = InheritResult()
    candidate_keys = list(keys) if keys is not None else list(base_vars.keys())

    updated_child = dict(child_vars)

    for key in candidate_keys:
        if key not in base_vars:
            continue
        value = base_vars[key]
        if key in child_vars:
            if overwrite:
                updated_child[key] = value
                result.overwritten.append(key)
            else:
                result.skipped.append(key)
        else:
            updated_child[key] = value
            result.inherited.append(key)

    if not dry_run and result.total_changes > 0:
        config.set_profile(child, updated_child)
        config.save()

    return result
