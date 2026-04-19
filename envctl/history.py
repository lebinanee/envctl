"""Track change history for environment variable keys."""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

HISTORY_FILE = Path(".envctl_history.json")


class HistoryError(Exception):
    pass


@dataclass
class HistoryEntry:
    profile: str
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    action: str  # set | delete | rename
    timestamp: float

    def to_dict(self) -> dict:
        return asdict(self)


def _load(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f)


def _save(path: Path, entries: List[dict]) -> None:
    with path.open("w") as f:
        json.dump(entries, f, indent=2)


def record(profile: str, key: str, old_value: Optional[str], new_value: Optional[str],
           action: str, path: Path = HISTORY_FILE) -> HistoryEntry:
    if action not in ("set", "delete", "rename"):
        raise HistoryError(f"Unknown action: {action}")
    entry = HistoryEntry(profile=profile, key=key, old_value=old_value,
                         new_value=new_value, action=action, timestamp=time.time())
    entries = _load(path)
    entries.append(entry.to_dict())
    _save(path, entries)
    return entry


def get_history(profile: Optional[str] = None, key: Optional[str] = None,
                path: Path = HISTORY_FILE) -> List[HistoryEntry]:
    raw = _load(path)
    results = []
    for r in raw:
        if profile and r["profile"] != profile:
            continue
        if key and r["key"] != key:
            continue
        results.append(HistoryEntry(**r))
    return results


def clear_history(path: Path = HISTORY_FILE) -> None:
    _save(path, [])
