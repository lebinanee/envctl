"""Apply value transformations to environment variable profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class TransformError(Exception):
    """Raised when a transformation fails."""


@dataclass
class TransformResult:
    applied: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_applied(self) -> int:
        return len(self.applied)


_BUILT_IN: Dict[str, Callable[[str], str]] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "trim_quotes": lambda v: v.strip("'\"" ),
}


def get_transform(name: str) -> Callable[[str], str]:
    """Return a built-in transform function by name."""
    if name not in _BUILT_IN:
        raise TransformError(
            f"Unknown transform '{name}'. Available: {', '.join(_BUILT_IN)}"
        )
    return _BUILT_IN[name]


def transform_profile(
    config,
    profile: str,
    transform_name: str,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> TransformResult:
    """Apply a named transform to all (or selected) keys in a profile."""
    fn = get_transform(transform_name)
    vars_ = config.get_profile(profile)
    if vars_ is None:
        raise TransformError(f"Profile '{profile}' not found.")

    result = TransformResult()
    updated = dict(vars_)

    for key, value in vars_.items():
        if keys and key not in keys:
            result.skipped.append(key)
            continue
        new_value = fn(value)
        if new_value == value:
            result.skipped.append(key)
        else:
            result.applied[key] = new_value
            updated[key] = new_value

    if not dry_run and result.applied:
        config.set_profile(profile, updated)
        config.save()

    return result
