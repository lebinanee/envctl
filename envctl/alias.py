"""Alias support: map short names to environment variable keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

ALIAS_FILENAME = ".envctl_aliases.json"


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _alias_path(config) -> Path:
    base = Path(config.path).parent
    return base / ALIAS_FILENAME


def _load_aliases(config) -> Dict[str, str]:
    path = _alias_path(config)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise AliasError(f"Failed to load aliases: {exc}") from exc


def _save_aliases(config, aliases: Dict[str, str]) -> None:
    path = _alias_path(config)
    try:
        path.write_text(json.dumps(aliases, indent=2))
    except OSError as exc:
        raise AliasError(f"Failed to save aliases: {exc}") from exc


def set_alias(config, alias: str, key: str) -> None:
    """Register *alias* as a short name for *key*."""
    if not alias or not alias.isidentifier():
        raise AliasError(f"Invalid alias name: {alias!r}")
    if not key:
        raise AliasError("Key must not be empty.")
    aliases = _load_aliases(config)
    aliases[alias] = key
    _save_aliases(config, aliases)


def remove_alias(config, alias: str) -> bool:
    """Remove *alias*. Returns True if it existed, False otherwise."""
    aliases = _load_aliases(config)
    if alias not in aliases:
        return False
    del aliases[alias]
    _save_aliases(config, aliases)
    return True


def resolve_alias(config, alias: str) -> Optional[str]:
    """Return the key mapped to *alias*, or None if not found."""
    return _load_aliases(config).get(alias)


def list_aliases(config) -> Dict[str, str]:
    """Return all registered aliases."""
    return _load_aliases(config)


def resolve_key(config, name: str) -> str:
    """Resolve *name* through aliases, returning the canonical key."""
    resolved = resolve_alias(config, name)
    return resolved if resolved is not None else name
