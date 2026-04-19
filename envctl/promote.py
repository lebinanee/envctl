"""Promote environment variables from one profile to another with optional key filtering."""

from typing import Optional
from envctl.config import Config
from envctl.validate import validate_key


class PromoteError(Exception):
    pass


def promote_keys(
    config: Config,
    src: str,
    dst: str,
    keys: Optional[list[str]] = None,
    overwrite: bool = False,
) -> dict[str, str]:
    """Promote keys from src profile to dst profile.

    Returns a dict of {key: status} where status is 'promoted', 'skipped', or 'overwritten'.
    """
    valid_envs = config.get_valid_envs()
    if src not in valid_envs:
        raise PromoteError(f"Source profile '{src}' is not valid.")
    if dst not in valid_envs:
        raise PromoteError(f"Destination profile '{dst}' is not valid.")
    if src == dst:
        raise PromoteError("Source and destination profiles must differ.")

    src_vars = config.get_profile(src) or {}
    dst_vars = config.get_profile(dst) or {}

    target_keys = keys if keys else list(src_vars.keys())
    results: dict[str, str] = {}

    for key in target_keys:
        validate_key(key)
        if key not in src_vars:
            raise PromoteError(f"Key '{key}' not found in profile '{src}'.")
        if key in dst_vars and not overwrite:
            results[key] = "skipped"
            continue
        status = "overwritten" if key in dst_vars else "promoted"
        dst_vars[key] = src_vars[key]
        results[key] = status

    config.set_profile(dst, dst_vars)
    config.save()
    return results
