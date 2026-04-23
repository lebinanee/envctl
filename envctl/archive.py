"""Archive and restore entire environment config snapshots as compressed bundles."""

from __future__ import annotations

import json
import zipfile
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envctl.config import Config


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_archive(config: Config, dest_dir: Path, label: Optional[str] = None) -> Path:
    """Serialize all profiles into a zip archive and write it to *dest_dir*.

    Returns the path of the created archive file.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    slug = label.replace(" ", "_") if label else "archive"
    filename = f"envctl_{slug}_{_timestamp()}.zip"
    archive_path = dest_dir / filename

    data = config._load()  # raw dict from config file
    profiles = data.get("profiles", {})
    if not profiles:
        raise ArchiveError("No profiles found; nothing to archive.")

    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "label": label or "",
        "profiles": list(profiles.keys()),
    }

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.json", json.dumps(meta, indent=2))
        for profile_name, vars_ in profiles.items():
            zf.writestr(f"profiles/{profile_name}.json", json.dumps(vars_, indent=2))

    return archive_path


def restore_archive(config: Config, archive_path: Path, overwrite: bool = False) -> dict[str, int]:
    """Load profiles from a zip archive into *config*.

    Returns a dict mapping profile name -> number of keys imported.
    Raises ArchiveError if the file is not a valid envctl archive.
    """
    archive_path = Path(archive_path)
    if not archive_path.exists():
        raise ArchiveError(f"Archive not found: {archive_path}")

    results: dict[str, int] = {}

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if "meta.json" not in names:
                raise ArchiveError("Not a valid envctl archive (missing meta.json).")

            profile_files = [n for n in names if n.startswith("profiles/") and n.endswith(".json")]
            for pf in profile_files:
                profile_name = Path(pf).stem
                vars_ = json.loads(zf.read(pf))
                existing = config.get_profile(profile_name) or {}
                merged = {**existing} if not overwrite else {}
                for key, value in vars_.items():
                    if overwrite or key not in merged:
                        merged[key] = value
                config.set_profile(profile_name, merged)
                results[profile_name] = len(vars_)
    except zipfile.BadZipFile as exc:
        raise ArchiveError(f"Invalid zip file: {exc}") from exc

    config.save()
    return results
