"""Audit log for environment variable changes."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

AUDIT_FILE = ".envctl_audit.json"


class AuditEntry:
    def __init__(self, action: str, env: str, key: str, old_value=None, new_value=None):
        self.timestamp = datetime.utcnow().isoformat()
        self.action = action
        self.env = env
        self.key = key
        self.old_value = old_value
        self.new_value = new_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "env": self.env,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


def _load_log(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_log(path: str, entries: List[Dict[str, Any]]) -> None:
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def record(entry: AuditEntry, path: str = AUDIT_FILE) -> None:
    """Append an audit entry to the log file."""
    entries = _load_log(path)
    entries.append(entry.to_dict())
    _save_log(path, entries)


def get_log(path: str = AUDIT_FILE) -> List[Dict[str, Any]]:
    """Return all audit log entries."""
    return _load_log(path)


def clear_log(path: str = AUDIT_FILE) -> None:
    """Clear the audit log."""
    _save_log(path, [])
