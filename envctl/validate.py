"""Validation helpers for environment variable keys and values."""

import re
from typing import Dict, List


class ValidationError(Exception):
    """Raised when environment variable validation fails."""
    pass


_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')


def validate_key(key: str) -> None:
    """Raise ValidationError if key is not a valid env var name."""
    if not key:
        raise ValidationError("Key must not be empty.")
    if not _KEY_RE.match(key):
        raise ValidationError(
            f"Invalid key '{key}': must match [A-Z_][A-Z0-9_]* (uppercase, digits, underscores)."
        )


def validate_value(value: str) -> None:
    """Raise ValidationError if value contains null bytes."""
    if '\x00' in value:
        raise ValidationError("Value must not contain null bytes.")


def validate_pair(key: str, value: str) -> None:
    """Validate both key and value."""
    validate_key(key)
    validate_value(value)


def validate_profile(profile: Dict[str, str]) -> List[str]:
    """Validate all key/value pairs in a profile dict.

    Returns a list of error messages (empty if all valid).
    """
    errors: List[str] = []
    for key, value in profile.items():
        try:
            validate_pair(key, value)
        except ValidationError as exc:
            errors.append(str(exc))
    return errors
