"""Rollback a profile to a previous snapshot."""
from __future__ import annotations
from typing import Optional
from envctl.config import Config
from envctl.snapshot import list_snapshots, SnapshotError


class RollbackError(Exception):
    pass


def rollback_profile(
    config: Config,
    profile: str,
    snapshot_id: str,
    dry_run: bool = False,
) -> dict:
    """Restore *profile* to the state captured in *snapshot_id*.

    Returns a dict with keys 'added', 'changed', 'removed' describing
    what would be (or was) applied.
    """
    snapshots = list_snapshots(config)
    match = next((s for s in snapshots if s["id"] == snapshot_id), None)
    if match is None:
        raise RollbackError(f"Snapshot '{snapshot_id}' not found.")

    snap_data: dict = match.get("profiles", {})
    if profile not in snap_data:
        raise RollbackError(
            f"Profile '{profile}' not present in snapshot '{snapshot_id}'."
        )

    target: dict = snap_data[profile]
    current: dict = config.get_profile(profile) or {}

    added = {k: v for k, v in target.items() if k not in current}
    changed = {k: v for k, v in target.items() if k in current and current[k] != v}
    removed = {k: current[k] for k in current if k not in target}

    if not dry_run:
        config.set_profile(profile, dict(target))
        config.save()

    return {"added": added, "changed": changed, "removed": removed}
