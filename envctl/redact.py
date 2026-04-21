"""Redact sensitive keys from a profile before sharing or exporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envctl.mask import is_sensitive


class RedactError(Exception):
    """Raised when redaction fails."""


@dataclass
class RedactResult:
    redacted: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    @property
    def total_redacted(self) -> int:
        return len(self.redacted_keys)


PLACEHOLDER = "[REDACTED]"


def redact_profile(
    config,
    profile: str,
    keys: Optional[List[str]] = None,
    auto: bool = True,
) -> RedactResult:
    """Return a copy of the profile vars with sensitive values replaced.

    Args:
        config: Config instance.
        profile: Profile name to redact.
        keys: Explicit list of keys to redact. If None and auto=True,
              sensitive keys are detected automatically.
        auto: When True, auto-detect sensitive keys via is_sensitive().

    Returns:
        RedactResult with the sanitised variable dict and metadata.
    """
    vars_: dict = config.get_profile(profile)
    if vars_ is None:
        raise RedactError(f"Profile '{profile}' not found.")

    redacted_vars: Dict[str, str] = {}
    redacted_keys: List[str] = []
    skipped_keys: List[str] = []

    explicit = set(keys) if keys else set()

    for k, v in vars_.items():
        if k in explicit or (auto and is_sensitive(k)):
            redacted_vars[k] = PLACEHOLDER
            redacted_keys.append(k)
        else:
            redacted_vars[k] = v
            skipped_keys.append(k)

    return RedactResult(
        redacted=redacted_vars,
        redacted_keys=sorted(redacted_keys),
        skipped_keys=sorted(skipped_keys),
    )
