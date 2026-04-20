"""Schema validation for environment variable profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from envctl.config import Config


class SchemaError(Exception):
    """Raised when schema validation fails."""


@dataclass
class SchemaField:
    key: str
    required: bool = True
    default: str | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "required": self.required,
            "default": self.default,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaField":
        return cls(
            key=data["key"],
            required=data.get("required", True),
            default=data.get("default"),
            description=data.get("description", ""),
        )


@dataclass
class SchemaViolation:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message}"


def get_schema(cfg: Config) -> list[SchemaField]:
    """Return the list of defined schema fields."""
    raw: list[dict] = cfg._data.get("schema", [])
    return [SchemaField.from_dict(r) for r in raw]


def set_schema(cfg: Config, fields: list[SchemaField]) -> None:
    """Persist schema fields into config."""
    cfg._data["schema"] = [f.to_dict() for f in fields]
    cfg.save()


def add_field(cfg: Config, field: SchemaField) -> None:
    """Add or replace a schema field by key."""
    fields = get_schema(cfg)
    fields = [f for f in fields if f.key != field.key]
    fields.append(field)
    set_schema(cfg, fields)


def remove_field(cfg: Config, key: str) -> bool:
    """Remove a schema field. Returns True if it existed."""
    fields = get_schema(cfg)
    new_fields = [f for f in fields if f.key != key]
    if len(new_fields) == len(fields):
        return False
    set_schema(cfg, new_fields)
    return True


def validate_against_schema(cfg: Config, profile: str) -> list[SchemaViolation]:
    """Check a profile against the defined schema."""
    fields = get_schema(cfg)
    if not fields:
        return []
    env_vars: dict[str, str] = cfg._data.get("profiles", {}).get(profile, {})
    violations: list[SchemaViolation] = []
    for f in fields:
        if f.key not in env_vars:
            if f.required and f.default is None:
                violations.append(SchemaViolation(f.key, "required key is missing"))
    return violations
