"""sanitize.py — Strip, normalize, and clean environment variable values.

Provides utilities to sanitize values in a profile: trimming whitespace,
removing control characters, normalizing line endings, and optionally
replacing empty values with a default.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional


class SanitizeError(Exception):
    """Raised when sanitization cannot be applied."""


@dataclass
class SanitizeResult:
    """Outcome of a sanitize operation on a profile."""

    profile: str
    changed: dict[str, tuple[str, str]] = field(default_factory=dict)  # key -> (before, after)
    skipped: list[str] = field(default_factory=list)  # keys whose values were unchanged

    @property
    def total_changed(self) -> int:
        return len(self.changed)


# Regex matching ASCII control characters (except tab/newline which we handle separately)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _strip_control_chars(value: str) -> str:
    """Remove ASCII control characters from *value*, preserving printable content."""
    return _CONTROL_CHARS_RE.sub("", value)


def _normalize_unicode(value: str) -> str:
    """Apply NFC unicode normalization to *value*."""
    return unicodedata.normalize("NFC", value)


def _collapse_whitespace(value: str) -> str:
    """Replace sequences of internal whitespace with a single space, then strip."""
    return re.sub(r"[ \t]+", " ", value).strip()


def sanitize_value(
    value: str,
    *,
    strip: bool = True,
    remove_control: bool = True,
    normalize_unicode: bool = True,
    collapse_internal: bool = False,
    default_empty: Optional[str] = None,
) -> str:
    """Return a sanitized copy of *value*.

    Parameters
    ----------
    value:            The raw string to sanitize.
    strip:            Trim leading/trailing whitespace.
    remove_control:   Strip ASCII control characters.
    normalize_unicode: Apply NFC normalization.
    collapse_internal: Collapse runs of internal whitespace to a single space.
    default_empty:    If the result is an empty string, substitute this value.
    """
    result = value

    if remove_control:
        result = _strip_control_chars(result)

    if normalize_unicode:
        result = _normalize_unicode(result)

    if collapse_internal:
        result = _collapse_whitespace(result)
    elif strip:
        result = result.strip()

    if default_empty is not None and result == "":
        result = default_empty

    return result


def sanitize_profile(
    config,
    profile: str,
    *,
    keys: Optional[list[str]] = None,
    dry_run: bool = False,
    strip: bool = True,
    remove_control: bool = True,
    normalize_unicode: bool = True,
    collapse_internal: bool = False,
    default_empty: Optional[str] = None,
) -> SanitizeResult:
    """Sanitize values in *profile* and persist changes unless *dry_run* is True.

    Parameters
    ----------
    config:   A ``Config`` instance.
    profile:  Name of the profile to sanitize.
    keys:     Restrict sanitization to these keys (``None`` means all keys).
    dry_run:  When ``True``, compute changes but do not write them back.

    All remaining keyword arguments are forwarded to :func:`sanitize_value`.

    Returns
    -------
    SanitizeResult with details of every changed and unchanged key.
    """
    vars_ = config.get_profile(profile)
    if vars_ is None:
        raise SanitizeError(f"Profile '{profile}' does not exist.")

    result = SanitizeResult(profile=profile)
    target_keys = keys if keys is not None else list(vars_.keys())

    updated: dict[str, str] = dict(vars_)

    for key in target_keys:
        if key not in vars_:
            continue
        original = vars_[key]
        cleaned = sanitize_value(
            original,
            strip=strip,
            remove_control=remove_control,
            normalize_unicode=normalize_unicode,
            collapse_internal=collapse_internal,
            default_empty=default_empty,
        )
        if cleaned != original:
            result.changed[key] = (original, cleaned)
            updated[key] = cleaned
        else:
            result.skipped.append(key)

    if result.changed and not dry_run:
        config.set_profile(profile, updated)
        config.save()

    return result
