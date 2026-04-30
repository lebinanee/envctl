"""Normalize environment variable values across profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class NormalizeError(Exception):
    """Raised when normalization fails."""


@dataclass
class NormalizeResult:
    applied: Dict[str, str] = field(default_factory=dict)   # key -> new value
    skipped: Dict[str, str] = field(default_factory=dict)   # key -> reason

    @property
    def total_applied(self) -> int:
        return len(self.applied)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)


_STRATEGIES = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "title": str.title,
}


def get_strategy(name: str):
    """Return a normalization function by name or raise NormalizeError."""
    fn = _STRATEGIES.get(name)
    if fn is None:
        raise NormalizeError(
            f"Unknown strategy '{name}'. Choose from: {', '.join(_STRATEGIES)}"
        )
    return fn


def normalize_profile(
    config,
    profile: str,
    strategy: str,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> NormalizeResult:
    """Apply a normalization strategy to values in *profile*.

    Args:
        config:   Config instance.
        profile:  Profile name to operate on.
        strategy: One of 'upper', 'lower', 'strip', 'title'.
        keys:     Optional list of keys to restrict transformation to.
        dry_run:  If True, compute changes without persisting them.

    Returns:
        NormalizeResult describing what changed.
    """
    fn = get_strategy(strategy)
    env = config.get_profile(profile)
    if env is None:
        raise NormalizeError(f"Profile '{profile}' not found.")

    result = NormalizeResult()
    target_keys = keys if keys else list(env.keys())

    updated = dict(env)
    for key in target_keys:
        if key not in env:
            result.skipped[key] = "key not found"
            continue
        old_val = env[key]
        new_val = fn(old_val)
        if new_val == old_val:
            result.skipped[key] = "no change"
        else:
            result.applied[key] = new_val
            updated[key] = new_val

    if result.applied and not dry_run:
        config.set_profile(profile, updated)
        config.save()

    return result
