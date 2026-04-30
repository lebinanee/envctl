"""Access control: restrict which keys a given role/user can read or write."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class AccessError(Exception):
    pass


def _access_path(cfg) -> Path:
    return Path(cfg.path).parent / ".envctl_access.json"


def _load_acl(cfg) -> Dict:
    p = _access_path(cfg)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_acl(cfg, acl: Dict) -> None:
    _access_path(cfg).write_text(json.dumps(acl, indent=2))


def set_access(cfg, profile: str, role: str, keys: List[str], mode: str = "read") -> None:
    """Grant a role access to specific keys in a profile.

    mode must be 'read' or 'write'.
    """
    if mode not in ("read", "write"):
        raise AccessError(f"Invalid mode '{mode}': must be 'read' or 'write'")
    if profile not in (cfg.get_active_env() and cfg.list_profiles() or cfg.list_profiles()):
        raise AccessError(f"Profile '{profile}' does not exist")
    acl = _load_acl(cfg)
    acl.setdefault(profile, {}).setdefault(role, {})[mode] = sorted(set(keys))
    _save_acl(cfg, acl)


def revoke_access(cfg, profile: str, role: str, mode: Optional[str] = None) -> bool:
    """Revoke a role's access entry. If mode is None, remove all modes."""
    acl = _load_acl(cfg)
    role_entry = acl.get(profile, {}).get(role)
    if role_entry is None:
        return False
    if mode is None:
        del acl[profile][role]
    else:
        acl[profile][role].pop(mode, None)
    _save_acl(cfg, acl)
    return True


def check_access(cfg, profile: str, role: str, key: str, mode: str = "read") -> bool:
    """Return True if the role can access the key in the given mode."""
    acl = _load_acl(cfg)
    allowed = acl.get(profile, {}).get(role, {}).get(mode, [])
    return key in allowed


def list_access(cfg, profile: str) -> Dict:
    """Return the full ACL dict for a profile."""
    acl = _load_acl(cfg)
    return acl.get(profile, {})
