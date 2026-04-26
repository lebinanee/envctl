"""Namespace support: group keys under logical prefixes within a profile."""
from __future__ import annotations

from typing import Dict, List, Optional

NS_SEP = "__"


class NamespaceError(Exception):
    pass


def _prefix(ns: str) -> str:
    return ns.upper().rstrip("_") + NS_SEP


def list_namespaces(profile: Dict[str, str]) -> List[str]:
    """Return sorted unique namespaces found in *profile*."""
    seen: set[str] = set()
    for key in profile:
        if NS_SEP in key:
            ns = key.split(NS_SEP)[0]
            seen.add(ns)
    return sorted(seen)


def get_namespace(
    profile: Dict[str, str], ns: str
) -> Dict[str, str]:
    """Return all key/value pairs whose key starts with *ns* prefix."""
    prefix = _prefix(ns)
    return {k: v for k, v in profile.items() if k.startswith(prefix)}


def set_namespace(
    profile: Dict[str, str],
    ns: str,
    pairs: Dict[str, str],
    overwrite: bool = False,
) -> Dict[str, int]:
    """Bulk-set *pairs* under *ns* prefix.  Returns counts: added/skipped."""
    if not ns or not ns.replace("_", "").isalpha():
        raise NamespaceError(f"Invalid namespace name: {ns!r}")
    prefix = _prefix(ns)
    added = skipped = 0
    for bare_key, value in pairs.items():
        full_key = prefix + bare_key.upper()
        if full_key in profile and not overwrite:
            skipped += 1
        else:
            profile[full_key] = value
            added += 1
    return {"added": added, "skipped": skipped}


def delete_namespace(profile: Dict[str, str], ns: str) -> int:
    """Remove all keys under *ns* from *profile*.  Returns count removed."""
    prefix = _prefix(ns)
    keys = [k for k in profile if k.startswith(prefix)]
    for k in keys:
        del profile[k]
    return len(keys)


def rename_namespace(
    profile: Dict[str, str], old_ns: str, new_ns: str
) -> int:
    """Rename every key from *old_ns* prefix to *new_ns* prefix."""
    if not new_ns or not new_ns.replace("_", "").isalpha():
        raise NamespaceError(f"Invalid namespace name: {new_ns!r}")
    old_prefix = _prefix(old_ns)
    new_prefix = _prefix(new_ns)
    keys = [k for k in list(profile) if k.startswith(old_prefix)]
    for k in keys:
        new_key = new_prefix + k[len(old_prefix):]
        profile[new_key] = profile.pop(k)
    return len(keys)
