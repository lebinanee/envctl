"""Group management: assign env var keys to named groups for bulk operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class GroupError(Exception):
    """Raised when a group operation fails."""


def _group_path(config) -> Path:
    return Path(config.path).parent / ".envctl_groups.json"


def _load_groups(config) -> Dict[str, List[str]]:
    p = _group_path(config)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return {}


def _save_groups(config, groups: Dict[str, List[str]]) -> None:
    _group_path(config).write_text(json.dumps(groups, indent=2))


def add_to_group(config, group: str, key: str) -> bool:
    """Add *key* to *group*. Returns True if newly added, False if already present."""
    groups = _load_groups(config)
    members = groups.setdefault(group, [])
    if key in members:
        return False
    members.append(key)
    _save_groups(config, groups)
    return True


def remove_from_group(config, group: str, key: str) -> bool:
    """Remove *key* from *group*. Returns True if removed, False if not found."""
    groups = _load_groups(config)
    members = groups.get(group, [])
    if key not in members:
        return False
    members.remove(key)
    if not members:
        del groups[group]
    else:
        groups[group] = members
    _save_groups(config, groups)
    return True


def get_group(config, group: str) -> List[str]:
    """Return list of keys belonging to *group*."""
    return list(_load_groups(config).get(group, []))


def list_groups(config) -> Dict[str, List[str]]:
    """Return all groups and their members."""
    return dict(_load_groups(config))


def delete_group(config, group: str) -> bool:
    """Delete an entire group. Returns True if deleted, False if not found."""
    groups = _load_groups(config)
    if group not in groups:
        return False
    del groups[group]
    _save_groups(config, groups)
    return True


def keys_for_groups(config, group_names: List[str]) -> List[str]:
    """Return deduplicated list of keys across multiple groups."""
    groups = _load_groups(config)
    seen = []
    for name in group_names:
        for key in groups.get(name, []):
            if key not in seen:
                seen.append(key)
    return seen
