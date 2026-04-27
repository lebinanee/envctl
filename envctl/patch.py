"""Patch module: apply a dict of key/value updates to a profile atomically."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envctl.validate import validate_pair, ValidationError


class PatchError(Exception):
    """Raised when a patch operation fails."""


@dataclass
class PatchResult:
    applied: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def total_applied(self) -> int:
        return len(self.applied)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)


def patch_profile(
    config,
    profile: str,
    patch: Dict[str, str],
    *,
    overwrite: bool = True,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> PatchResult:
    """Apply *patch* to *profile* in *config*.

    Args:
        config: Config instance.
        profile: Target profile name.
        patch: Mapping of key -> new value.
        overwrite: When False, skip keys that already exist.
        keys: If provided, only patch these keys (subset of patch).
        dry_run: If True, compute result without mutating config.

    Returns:
        PatchResult describing what was applied / skipped.

    Raises:
        PatchError: If the profile does not exist.
    """
    existing = config.get_profile(profile)
    if existing is None:
        raise PatchError(f"Profile '{profile}' does not exist.")

    result = PatchResult()
    working = dict(existing)

    items = {k: v for k, v in patch.items() if keys is None or k in keys}

    for key, value in items.items():
        try:
            validate_pair(key, value)
        except ValidationError as exc:
            result.errors.append(str(exc))
            continue

        if not overwrite and key in working:
            result.skipped[key] = value
            continue

        result.applied[key] = value
        working[key] = value

    if not dry_run and result.applied:
        config.set_profile(profile, working)
        config.save()

    return result
