"""Copy keys between profiles."""
from typing import Optional, List
from envctl.config import Config
from envctl.validate import validate_key


class CopyError(Exception):
    pass


def copy_keys(
    config: Config,
    src: str,
    dst: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> dict:
    """Copy keys from src profile to dst profile.

    Returns a dict with 'copied' and 'skipped' key lists.
    """
    src_data = config.get_profile(src)
    if src_data is None:
        raise CopyError(f"Source profile '{src}' not found.")

    dst_data = config.get_profile(dst)
    if dst_data is None:
        raise CopyError(f"Destination profile '{dst}' not found.")

    target_keys = keys if keys else list(src_data.keys())
    for k in target_keys:
        validate_key(k)

    copied = []
    skipped = []

    for key in target_keys:
        if key not in src_data:
            raise CopyError(f"Key '{key}' not found in source profile '{src}'.")
        if key in dst_data and not overwrite:
            skipped.append(key)
        else:
            dst_data[key] = src_data[key]
            copied.append(key)

    config.set_profile(dst, dst_data)
    config.save()
    return {"copied": copied, "skipped": skipped}
