"""Blueprint: save and apply a named set of key definitions as a reusable template."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

BLUEPRINT_FILE = ".envctl_blueprints.json"


class BlueprintError(Exception):
    """Raised when a blueprint operation fails."""


@dataclass
class Blueprint:
    name: str
    keys: Dict[str, str] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "keys": self.keys, "description": self.description}

    @classmethod
    def from_dict(cls, data: dict) -> "Blueprint":
        return cls(
            name=data["name"],
            keys=data.get("keys", {}),
            description=data.get("description", ""),
        )


def _blueprint_path(config) -> Path:
    return Path(config.path).parent / BLUEPRINT_FILE


def _load(config) -> Dict[str, Blueprint]:
    p = _blueprint_path(config)
    if not p.exists():
        return {}
    raw = json.loads(p.read_text())
    return {name: Blueprint.from_dict(entry) for name, entry in raw.items()}


def _save(config, blueprints: Dict[str, Blueprint]) -> None:
    p = _blueprint_path(config)
    p.write_text(json.dumps({k: v.to_dict() for k, v in blueprints.items()}, indent=2))


def save_blueprint(config, name: str, keys: Dict[str, str], description: str = "") -> Blueprint:
    """Persist a blueprint under *name*."""
    if not name or not name.isidentifier():
        raise BlueprintError(f"Invalid blueprint name: {name!r}")
    blueprints = _load(config)
    bp = Blueprint(name=name, keys=dict(keys), description=description)
    blueprints[name] = bp
    _save(config, blueprints)
    return bp


def get_blueprint(config, name: str) -> Blueprint:
    blueprints = _load(config)
    if name not in blueprints:
        raise BlueprintError(f"Blueprint {name!r} not found")
    return blueprints[name]


def list_blueprints(config) -> List[Blueprint]:
    return sorted(_load(config).values(), key=lambda b: b.name)


def delete_blueprint(config, name: str) -> bool:
    blueprints = _load(config)
    if name not in blueprints:
        return False
    del blueprints[name]
    _save(config, blueprints)
    return True


def apply_blueprint(config, name: str, profile: str, overwrite: bool = False) -> Dict[str, str]:
    """Apply blueprint keys to *profile*. Returns dict of keys actually written."""
    bp = get_blueprint(config, name)
    existing = config.get_profile(profile) or {}
    applied: Dict[str, str] = {}
    for key, value in bp.keys.items():
        if key in existing and not overwrite:
            continue
        existing[key] = value
        applied[key] = value
    if applied:
        config.set_profile(profile, existing)
        config.save()
    return applied
