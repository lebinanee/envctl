"""Snapshot feature: save and restore environment profiles at a point in time."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

SNAPSHOT_FILE = ".envctl_snapshots.json"


class SnapshotError(Exception):
    pass


def _load_snapshots(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_snapshots(path: str, snapshots: List[dict]) -> None:
    with open(path, "w") as f:
        json.dump(snapshots, f, indent=2)


def take_snapshot(config, env: str, label: Optional[str] = None, path: str = SNAPSHOT_FILE) -> dict:
    """Save current state of an environment profile as a snapshot."""
    profile = config.get_profile(env)
    if profile is None:
        raise SnapshotError(f"Environment '{env}' has no variables to snapshot.")
    snapshots = _load_snapshots(path)
    entry = {
        "env": env,
        "label": label or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vars": dict(profile),
    }
    snapshots.append(entry)
    _save_snapshots(path, snapshots)
    return entry


def list_snapshots(env: Optional[str] = None, path: str = SNAPSHOT_FILE) -> List[dict]:
    """Return snapshots, optionally filtered by environment."""
    snapshots = _load_snapshots(path)
    if env:
        snapshots = [s for s in snapshots if s["env"] == env]
    return snapshots


def restore_snapshot(config, index: int, path: str = SNAPSHOT_FILE) -> dict:
    """Restore a snapshot by its list index and return the restored entry."""
    snapshots = _load_snapshots(path)
    if index < 0 or index >= len(snapshots):
        raise SnapshotError(f"Snapshot index {index} out of range (total: {len(snapshots)}).")
    entry = snapshots[index]
    config.set_profile(entry["env"], entry["vars"])
    config.save()
    return entry


def delete_snapshot(index: int, path: str = SNAPSHOT_FILE) -> None:
    """Delete a snapshot by its list index."""
    snapshots = _load_snapshots(path)
    if index < 0 or index >= len(snapshots):
        raise SnapshotError(f"Snapshot index {index} out of range (total: {len(snapshots)}).")
    snapshots.pop(index)
    _save_snapshots(path, snapshots)
