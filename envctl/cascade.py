"""Cascade: resolve effective env vars by layering profiles (base → override)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CascadeError(Exception):
    """Raised when cascade resolution fails."""


@dataclass
class CascadeResult:
    effective: Dict[str, str] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)  # key -> profile it came from
    overridden: Dict[str, List[str]] = field(default_factory=dict)  # key -> profiles that had it

    @property
    def total_keys(self) -> int:
        return len(self.effective)


def cascade_profiles(
    config,
    profiles: List[str],
    keys: Optional[List[str]] = None,
) -> CascadeResult:
    """Layer *profiles* left-to-right; later profiles override earlier ones.

    Args:
        config: Config instance with a ``get_profile(name)`` method.
        profiles: Ordered list of profile names, lowest to highest priority.
        keys: If given, restrict output to these keys only.

    Returns:
        CascadeResult with merged vars and provenance metadata.
    """
    if not profiles:
        raise CascadeError("At least one profile must be specified.")

    result = CascadeResult()

    for profile_name in profiles:
        profile = config.get_profile(profile_name)
        if profile is None:
            raise CascadeError(f"Profile '{profile_name}' not found.")

        for k, v in profile.items():
            if keys and k not in keys:
                continue
            if k in result.effective:
                result.overridden.setdefault(k, [result.sources[k]])
                result.overridden[k].append(profile_name)
            result.effective[k] = v
            result.sources[k] = profile_name

    return result


def format_cascade_report(result: CascadeResult) -> str:
    """Return a human-readable report of the cascade result."""
    if not result.effective:
        return "No variables resolved."

    lines: List[str] = []
    for key in sorted(result.effective):
        value = result.effective[key]
        source = result.sources[key]
        overrides = result.overridden.get(key, [])
        note = f"  (overrode: {', '.join(overrides[:-1])})" if overrides else ""
        lines.append(f"{key}={value}  [from: {source}]{note}")
    return "\n".join(lines)
