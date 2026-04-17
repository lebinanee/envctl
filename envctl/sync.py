"""Sync environment variables between local, staging, and production configs."""

import copy
from typing import Optional

ENVIRONMENTS = ["local", "staging", "production"]


class SyncError(Exception):
    pass


def diff_envs(source: dict, target: dict) -> dict:
    """Return keys that differ or are missing between source and target."""
    added = {k: v for k, v in source.items() if k not in target}
    removed = {k: v for k, v in target.items() if k not in source}
    changed = {
        k: {"from": target[k], "to": v}
        for k, v in source.items()
        if k in target and target[k] != v
    }
    return {"added": added, "removed": removed, "changed": changed}


def sync_envs(
    config,
    source_env: str,
    target_env: str,
    keys: Optional[list] = None,
    dry_run: bool = False,
) -> dict:
    """Sync variables from source_env to target_env.

    Args:
        config: Config instance.
        source_env: Environment to copy from.
        target_env: Environment to copy to.
        keys: Optional list of specific keys to sync. Syncs all if None.
        dry_run: If True, return diff without applying changes.

    Returns:
        A dict describing the changes made (or that would be made).
    """
    for env in (source_env, target_env):
        if env not in ENVIRONMENTS:
            raise SyncError(f"Unknown environment: '{env}'")

    if source_env == target_env:
        raise SyncError("Source and target environments must differ.")

    source_vars = copy.deepcopy(config.get_profile(source_env))
    target_vars = copy.deepcopy(config.get_profile(target_env))

    if keys:
        missing = [k for k in keys if k not in source_vars]
        if missing:
            raise SyncError(f"Keys not found in '{source_env}': {missing}")
        source_subset = {k: source_vars[k] for k in keys}
    else:
        source_subset = source_vars

    changes = diff_envs(source_subset, {k: target_vars.get(k) for k in source_subset})

    if not dry_run:
        for k, v in source_subset.items():
            target_vars[k] = v
        config.set_profile(target_env, target_vars)
        config.save()

    return changes
