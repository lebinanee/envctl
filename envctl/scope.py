"""Scope management: restrict which keys are visible/active per environment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class ScopeError(Exception):
    """Raised when a scope operation fails."""


_SCOPE_FILE = ".envctl_scopes.json"


def _load_scopes(config_dir: str) -> Dict[str, List[str]]:
    path = Path(config_dir) / _SCOPE_FILE
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_scopes(config_dir: str, scopes: Dict[str, List[str]]) -> None:
    path = Path(config_dir) / _SCOPE_FILE
    with open(path, "w") as f:
        json.dump(scopes, f, indent=2)


def set_scope(config_dir: str, profile: str, keys: List[str]) -> None:
    """Set the allowed key scope for a profile. Empty list clears the scope."""
    if not profile:
        raise ScopeError("Profile name must not be empty.")
    scopes = _load_scopes(config_dir)
    if keys:
        scopes[profile] = sorted(set(keys))
    else:
        scopes.pop(profile, None)
    _save_scopes(config_dir, scopes)


def get_scope(config_dir: str, profile: str) -> Optional[List[str]]:
    """Return the scope for a profile, or None if no scope is defined."""
    scopes = _load_scopes(config_dir)
    return scopes.get(profile)


def apply_scope(profile_vars: Dict[str, str], scope: Optional[List[str]]) -> Dict[str, str]:
    """Filter profile vars to only include keys in scope. If scope is None, return all."""
    if scope is None:
        return dict(profile_vars)
    return {k: v for k, v in profile_vars.items() if k in scope}


def list_scopes(config_dir: str) -> Dict[str, List[str]]:
    """Return all defined scopes."""
    return _load_scopes(config_dir)
