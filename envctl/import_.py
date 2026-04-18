"""Import environment variables from .env files into a profile."""

from pathlib import Path
from typing import Optional

from envctl.validate import validate_pair, ValidationError


class ImportError(Exception):
    pass


def parse_dotenv(path: str) -> dict:
    """Parse a .env file and return key-value pairs."""
    result = {}
    file = Path(path)
    if not file.exists():
        raise ImportError(f"File not found: {path}")

    for lineno, raw in enumerate(file.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ImportError(f"Invalid format on line {lineno}: {raw!r}")
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        try:
            validate_pair(key, value)
        except ValidationError as e:
            raise ImportError(f"Validation error on line {lineno}: {e}")
        result[key] = value

    return result


def import_into_profile(
    config,
    env: str,
    path: str,
    overwrite: bool = False,
    dry_run: bool = False,
) -> dict:
    """Import parsed .env vars into a config profile. Returns summary dict."""
    pairs = parse_dotenv(path)
    existing = config.get_profile(env) or {}

    added, skipped, updated = [], [], []
    for key, value in pairs.items():
        if key in existing:
            if overwrite:
                updated.append(key)
            else:
                skipped.append(key)
                continue
        else:
            added.append(key)
        if not dry_run:
            config.set_var(env, key, value)

    if not dry_run:
        config.save()

    return {"added": added, "updated": updated, "skipped": skipped}
