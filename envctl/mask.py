"""Mask/unmask sensitive environment variable values."""

from __future__ import annotations
from typing import List, Optional
from envctl.config import Config

SENSITIVE_PATTERNS = ["SECRET", "PASSWORD", "PASSWD", "TOKEN", "KEY", "PRIVATE", "AUTH", "CREDENTIAL"]
MASK_CHAR = "*"
VISIBLE_CHARS = 4


class MaskError(Exception):
    pass


def is_sensitive(key: str) -> bool:
    """Return True if the key name looks sensitive."""
    upper = key.upper()
    return any(pat in upper for pat in SENSITIVE_PATTERNS)


def mask_value(value: str, visible: int = VISIBLE_CHARS) -> str:
    """Mask a value, leaving only the last `visible` characters visible."""
    if len(value) <= visible:
        return MASK_CHAR * len(value)
    return MASK_CHAR * (len(value) - visible) + value[-visible:]


def mask_profile(config: Config, profile: str, keys: Optional[List[str]] = None) -> dict:
    """Return a dict of key->masked_value for the given profile.

    If keys is provided, only those keys are included; otherwise all keys.
    Sensitive keys are auto-masked; non-sensitive keys are returned as-is.
    """
    data = config.data.get("profiles", {}).get(profile)
    if data is None:
        raise MaskError(f"Profile '{profile}' not found.")

    result = {}
    targets = keys if keys else list(data.keys())
    for k in targets:
        if k not in data:
            raise MaskError(f"Key '{k}' not found in profile '{profile}'.")
        val = data[k]
        result[k] = mask_value(val) if is_sensitive(k) else val
    return result
