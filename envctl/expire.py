"""Expiry tracking for environment variable keys."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

EXPIRY_FILE = ".envctl_expiry.json"


class ExpireError(Exception):
    """Raised when an expiry operation fails."""


@dataclass
class ExpiryEntry:
    profile: str
    key: str
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "key": self.key,
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryEntry":
        return cls(
            profile=data["profile"],
            key=data["key"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )


def _load(path: Path) -> list[ExpiryEntry]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    return [ExpiryEntry.from_dict(d) for d in raw]


def _save(path: Path, entries: list[ExpiryEntry]) -> None:
    path.write_text(json.dumps([e.to_dict() for e in entries], indent=2))


def set_expiry(config, profile: str, key: str, expires_at: datetime,
               expiry_path: Optional[Path] = None) -> ExpiryEntry:
    """Attach an expiry datetime to a key in a profile."""
    prof = config.get_profile(profile)
    if prof is None or key not in prof:
        raise ExpireError(f"Key '{key}' not found in profile '{profile}'")
    path = expiry_path or Path(config.path).parent / EXPIRY_FILE
    entries = [e for e in _load(path) if not (e.profile == profile and e.key == key)]
    entry = ExpiryEntry(profile=profile, key=key, expires_at=expires_at)
    entries.append(entry)
    _save(path, entries)
    return entry


def get_expired(config, profile: str, expiry_path: Optional[Path] = None) -> list[ExpiryEntry]:
    """Return all expired entries for a profile."""
    path = expiry_path or Path(config.path).parent / EXPIRY_FILE
    entries = _load(path)
    return [e for e in entries if e.profile == profile and e.is_expired()]


def remove_expiry(config, profile: str, key: str,
                  expiry_path: Optional[Path] = None) -> bool:
    """Remove expiry tracking for a key. Returns True if an entry was removed."""
    path = expiry_path or Path(config.path).parent / EXPIRY_FILE
    entries = _load(path)
    filtered = [e for e in entries if not (e.profile == profile and e.key == key)]
    if len(filtered) == len(entries):
        return False
    _save(path, filtered)
    return True


def list_expiries(config, profile: str, expiry_path: Optional[Path] = None) -> list[ExpiryEntry]:
    """Return all expiry entries for a profile."""
    path = expiry_path or Path(config.path).parent / EXPIRY_FILE
    return [e for e in _load(path) if e.profile == profile]
