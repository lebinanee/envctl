"""Annotation support: attach human-readable notes to individual env keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


class AnnotateError(Exception):
    """Raised when an annotation operation fails."""


def _annotation_path(config) -> Path:
    return Path(config.path).parent / ".envctl" / "annotations.json"


def _load(config) -> Dict[str, Dict[str, str]]:
    """Return {profile: {key: note}} mapping."""
    p = _annotation_path(config)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise AnnotateError(f"Failed to load annotations: {exc}") from exc


def _save(config, data: Dict[str, Dict[str, str]]) -> None:
    p = _annotation_path(config)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def set_annotation(config, profile: str, key: str, note: str) -> None:
    """Attach *note* to *key* in *profile*."""
    env = config.get_profile(profile)
    if env is None:
        raise AnnotateError(f"Profile '{profile}' not found.")
    if key not in env:
        raise AnnotateError(f"Key '{key}' not found in profile '{profile}'.")
    data = _load(config)
    data.setdefault(profile, {})[key] = note
    _save(config, data)


def get_annotation(config, profile: str, key: str) -> Optional[str]:
    """Return the note for *key* in *profile*, or None."""
    data = _load(config)
    return data.get(profile, {}).get(key)


def remove_annotation(config, profile: str, key: str) -> bool:
    """Remove annotation for *key* in *profile*. Returns True if removed."""
    data = _load(config)
    removed = data.get(profile, {}).pop(key, None)
    if removed is not None:
        _save(config, data)
        return True
    return False


def list_annotations(config, profile: str) -> Dict[str, str]:
    """Return all annotations for *profile*."""
    data = _load(config)
    return dict(data.get(profile, {}))
