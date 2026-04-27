"""Resolve environment variable references within a profile.

Supports ${VAR} and $VAR syntax for cross-variable interpolation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}|\$([A-Z_][A-Z0-9_]*)")


class ResolveError(Exception):
    """Raised when variable resolution fails."""


@dataclass
class ResolveResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved: List[str] = field(default_factory=list)
    cycles: List[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.unresolved or self.cycles)


def _refs(value: str) -> List[str]:
    """Return all variable names referenced in *value*."""
    return [m.group(1) or m.group(2) for m in VAR_PATTERN.finditer(value)]


def _interpolate(value: str, env: Dict[str, str]) -> str:
    def replacer(m: re.Match) -> str:
        name = m.group(1) or m.group(2)
        return env.get(name, m.group(0))

    return VAR_PATTERN.sub(replacer, value)


def resolve_profile(
    profile: Dict[str, str],
    max_passes: int = 10,
) -> ResolveResult:
    """Resolve all cross-references in *profile* using iterative substitution.

    Args:
        profile: Mapping of key -> raw value (may contain ``${VAR}`` refs).
        max_passes: Maximum substitution iterations before declaring a cycle.

    Returns:
        :class:`ResolveResult` with fully-resolved values and any issues.
    """
    if not profile:
        return ResolveResult()

    env: Dict[str, str] = dict(profile)
    known = set(profile)

    for _ in range(max_passes):
        changed = False
        for key, val in env.items():
            new_val = _interpolate(val, env)
            if new_val != val:
                env[key] = new_val
                changed = True
        if not changed:
            break

    result = ResolveResult(resolved=env)

    for key, val in env.items():
        remaining = _refs(val)
        for ref in remaining:
            if ref in known:
                if ref not in result.cycles:
                    result.cycles.append(ref)
            else:
                if ref not in result.unresolved:
                    result.unresolved.append(ref)

    return result
