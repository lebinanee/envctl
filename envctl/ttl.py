"""TTL (time-to-live) management for environment variable keys."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

TTL_FILE = ".envctl_ttl.json"


class TTLError(Exception):
    """Raised when a TTL operation fails."""


class TTLEntry:
    def __init__(self, key: str, profile: str, expires_at: str) -> None:
        self.key = key
        self.profile = profile
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        return datetime.utcnow() >= datetime.fromisoformat(self.expires_at)

    def to_dict(self) -> dict:
        return {"key": self.key, "profile": self.profile, "expires_at": self.expires_at}

    @classmethod
    def from_dict(cls, data: dict) -> "TTLEntry":
        return cls(data["key"], data["profile"], data["expires_at"])


def _ttl_path(config_path: str) -> Path:
    return Path(config_path).parent / TTL_FILE


def _load(config_path: str) -> List[TTLEntry]:
    p = _ttl_path(config_path)
    if not p.exists():
        return []
    return [TTLEntry.from_dict(d) for d in json.loads(p.read_text())]


def _save(config_path: str, entries: List[TTLEntry]) -> None:
    _ttl_path(config_path).write_text(json.dumps([e.to_dict() for e in entries], indent=2))


def set_ttl(config, profile: str, key: str, seconds: int) -> TTLEntry:
    """Attach a TTL to a key in a profile."""
    vars_ = config.get_profile(profile)
    if key not in vars_:
        raise TTLError(f"Key '{key}' not found in profile '{profile}'")
    entries = _load(config.path)
    entries = [e for e in entries if not (e.key == key and e.profile == profile)]
    expires_at = (datetime.utcnow() + timedelta(seconds=seconds)).isoformat()
    entry = TTLEntry(key, profile, expires_at)
    entries.append(entry)
    _save(config.path, entries)
    return entry


def get_ttl(config, profile: str, key: str) -> Optional[TTLEntry]:
    """Return the TTL entry for a key, or None if not set."""
    for e in _load(config.path):
        if e.key == key and e.profile == profile:
            return e
    return None


def purge_expired(config, profile: str) -> List[str]:
    """Remove expired keys from a profile and their TTL entries. Returns removed key names."""
    entries = _load(config.path)
    expired = [e for e in entries if e.profile == profile and e.is_expired()]
    if not expired:
        return []
    vars_ = config.get_profile(profile)
    for e in expired:
        vars_.pop(e.key, None)
    config.set_profile(profile, vars_)
    config.save()
    remaining = [e for e in entries if not (e.profile == profile and e.is_expired())]
    _save(config.path, remaining)
    return [e.key for e in expired]


def list_ttls(config, profile: str) -> List[TTLEntry]:
    """List all TTL entries for a given profile."""
    return [e for e in _load(config.path) if e.profile == profile]
