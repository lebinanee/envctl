"""Notification hooks for envctl — fire callbacks when profile vars change."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class NotifyError(Exception):
    """Raised when a notification operation fails."""


@dataclass
class NotifyRule:
    profile: str
    keys: List[str]  # empty list means "all keys"
    webhook_url: str
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "keys": self.keys,
            "webhook_url": self.webhook_url,
            "label": self.label,
        }

    @staticmethod
    def from_dict(data: dict) -> "NotifyRule":
        return NotifyRule(
            profile=data["profile"],
            keys=data.get("keys", []),
            webhook_url=data["webhook_url"],
            label=data.get("label"),
        )


def _rules_path(config) -> Path:
    return Path(config.path).parent / ".envctl_notify.json"


def _load_rules(config) -> List[NotifyRule]:
    p = _rules_path(config)
    if not p.exists():
        return []
    return [NotifyRule.from_dict(d) for d in json.loads(p.read_text())]


def _save_rules(config, rules: List[NotifyRule]) -> None:
    _rules_path(config).write_text(json.dumps([r.to_dict() for r in rules], indent=2))


def add_rule(config, profile: str, webhook_url: str,
             keys: Optional[List[str]] = None, label: Optional[str] = None) -> NotifyRule:
    if profile not in config.list_envs():
        raise NotifyError(f"Profile '{profile}' does not exist.")
    rules = _load_rules(config)
    rule = NotifyRule(profile=profile, keys=keys or [], webhook_url=webhook_url, label=label)
    rules.append(rule)
    _save_rules(config, rules)
    return rule


def remove_rule(config, profile: str, webhook_url: str) -> bool:
    rules = _load_rules(config)
    new_rules = [r for r in rules if not (r.profile == profile and r.webhook_url == webhook_url)]
    if len(new_rules) == len(rules):
        return False
    _save_rules(config, new_rules)
    return True


def list_rules(config, profile: Optional[str] = None) -> List[NotifyRule]:
    rules = _load_rules(config)
    if profile:
        rules = [r for r in rules if r.profile == profile]
    return rules


def matching_rules(config, profile: str, changed_keys: List[str]) -> List[NotifyRule]:
    """Return rules that match the given profile and at least one changed key."""
    result = []
    for rule in _load_rules(config):
        if rule.profile != profile:
            continue
        if not rule.keys or any(k in rule.keys for k in changed_keys):
            result.append(rule)
    return result
