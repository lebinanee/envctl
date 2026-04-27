"""Mark environment variable keys as deprecated with optional replacement hints."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


class DeprecateError(Exception):
    pass


@dataclass
class DeprecationEntry:
    key: str
    profile: str
    reason: str
    replacement: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "profile": self.profile,
            "reason": self.reason,
            "replacement": self.replacement,
        }

    @staticmethod
    def from_dict(d: dict) -> "DeprecationEntry":
        return DeprecationEntry(
            key=d["key"],
            profile=d["profile"],
            reason=d["reason"],
            replacement=d.get("replacement"),
        )


def _deprecation_path(config) -> Path:
    return Path(config.path).parent / ".envctl_deprecations.json"


def _load(config) -> List[DeprecationEntry]:
    p = _deprecation_path(config)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [DeprecationEntry.from_dict(e) for e in data]


def _save(config, entries: List[DeprecationEntry]) -> None:
    p = _deprecation_path(config)
    p.write_text(json.dumps([e.to_dict() for e in entries], indent=2))


def mark_deprecated(
    config,
    profile: str,
    key: str,
    reason: str,
    replacement: Optional[str] = None,
) -> DeprecationEntry:
    if not config.get_profile(profile):
        raise DeprecateError(f"Profile '{profile}' not found.")
    vars_ = config.get_profile(profile)
    if key not in vars_:
        raise DeprecateError(f"Key '{key}' not found in profile '{profile}'.")
    entries = _load(config)
    entries = [e for e in entries if not (e.key == key and e.profile == profile)]
    entry = DeprecationEntry(key=key, profile=profile, reason=reason, replacement=replacement)
    entries.append(entry)
    _save(config, entries)
    return entry


def unmark_deprecated(config, profile: str, key: str) -> bool:
    entries = _load(config)
    before = len(entries)
    entries = [e for e in entries if not (e.key == key and e.profile == profile)]
    if len(entries) == before:
        return False
    _save(config, entries)
    return True


def list_deprecated(config, profile: Optional[str] = None) -> List[DeprecationEntry]:
    entries = _load(config)
    if profile:
        entries = [e for e in entries if e.profile == profile]
    return entries


def check_deprecated(config, profile: str) -> Dict[str, DeprecationEntry]:
    """Return a mapping of key -> entry for all deprecated keys present in profile."""
    entries = {e.key: e for e in _load(config) if e.profile == profile}
    vars_ = config.get_profile(profile) or {}
    return {k: v for k, v in entries.items() if k in vars_}
