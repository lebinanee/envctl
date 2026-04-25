"""Checkpoint: named restore points combining snapshot + audit metadata."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

CHECKPOINT_FILE = ".envctl_checkpoints.json"


class CheckpointError(Exception):
    pass


def _checkpoint_path(cfg) -> Path:
    return Path(cfg.path).parent / CHECKPOINT_FILE


def _load(cfg) -> dict[str, Any]:
    p = _checkpoint_path(cfg)
    if not p.exists():
        return {}
    with p.open() as f:
        return json.load(f)


def _save(cfg, data: dict[str, Any]) -> None:
    with _checkpoint_path(cfg).open("w") as f:
        json.dump(data, f, indent=2)


def create_checkpoint(cfg, profile: str, name: str, note: str = "") -> dict[str, Any]:
    """Save current profile state as a named checkpoint."""
    env = cfg.get_profile(profile)
    if env is None:
        raise CheckpointError(f"Profile '{profile}' not found")
    if not name.strip():
        raise CheckpointError("Checkpoint name must not be empty")

    data = _load(cfg)
    key = f"{profile}:{name}"
    entry = {
        "profile": profile,
        "name": name,
        "note": note,
        "timestamp": time.time(),
        "vars": dict(env),
    }
    data[key] = entry
    _save(cfg, data)
    return entry


def list_checkpoints(cfg, profile: str | None = None) -> list[dict[str, Any]]:
    """Return all checkpoints, optionally filtered by profile."""
    data = _load(cfg)
    entries = list(data.values())
    if profile:
        entries = [e for e in entries if e["profile"] == profile]
    return sorted(entries, key=lambda e: e["timestamp"])


def restore_checkpoint(cfg, profile: str, name: str) -> dict[str, str]:
    """Restore a profile to a named checkpoint state."""
    data = _load(cfg)
    key = f"{profile}:{name}"
    if key not in data:
        raise CheckpointError(f"Checkpoint '{name}' not found for profile '{profile}'")
    saved_vars: dict[str, str] = data[key]["vars"]
    cfg.set_profile(profile, saved_vars)
    cfg.save()
    return saved_vars


def delete_checkpoint(cfg, profile: str, name: str) -> bool:
    """Delete a named checkpoint. Returns True if deleted, False if not found."""
    data = _load(cfg)
    key = f"{profile}:{name}"
    if key not in data:
        return False
    del data[key]
    _save(cfg, data)
    return True
