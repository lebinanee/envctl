"""Clone an entire profile into a new profile."""
from __future__ import annotations
from typing import Optional
from envctl.config import Config


class CloneError(Exception):
    pass


def clone_profile(
    config: Config,
    src: str,
    dest: str,
    overwrite: bool = False,
) -> int:
    """Copy all keys from *src* profile into *dest* profile.

    Returns the number of keys written.
    Raises CloneError if *src* does not exist or *dest* already exists
    (unless *overwrite* is True).
    """
    valid = config.get("envs", default=["local", "staging", "production"])
    src_data: Optional[dict] = config.get_profile(src)
    if src_data is None:
        raise CloneError(f"Source profile '{src}' does not exist.")

    dest_data = config.get_profile(dest)
    if dest_data is not None and not overwrite:
        raise CloneError(
            f"Destination profile '{dest}' already exists. "
            "Use --overwrite to replace it."
        )

    new_profile = dict(src_data)
    config.set_profile(dest, new_profile)
    config.save()
    return len(new_profile)
