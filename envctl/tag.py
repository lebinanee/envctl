"""Tag management for environment variable keys."""
from __future__ import annotations
from typing import Dict, List
from envctl.config import Config
from envctl.validate import validate_key


class TagError(Exception):
    pass


TAGS_KEY = "__tags__"


def _get_tags(config: Config, profile: str) -> Dict[str, List[str]]:
    data = config.get_profile(profile) or {}
    raw = data.get(TAGS_KEY, {})
    return raw if isinstance(raw, dict) else {}


def _save_tags(config: Config, profile: str, tags: Dict[str, List[str]]) -> None:
    data = config.get_profile(profile) or {}
    data[TAGS_KEY] = tags
    config.set_profile(profile, data)
    config.save()


def add_tag(config: Config, profile: str, key: str, tag: str) -> None:
    validate_key(key)
    data = config.get_profile(profile) or {}
    if key not in data:
        raise TagError(f"Key '{key}' not found in profile '{profile}'")
    tags = _get_tags(config, profile)
    entry = tags.setdefault(key, [])
    if tag not in entry:
        entry.append(tag)
    _save_tags(config, profile, tags)


def remove_tag(config: Config, profile: str, key: str, tag: str) -> bool:
    tags = _get_tags(config, profile)
    entry = tags.get(key, [])
    if tag not in entry:
        return False
    entry.remove(tag)
    if not entry:
        del tags[key]
    _save_tags(config, profile, tags)
    return True


def list_tags(config: Config, profile: str, key: str) -> List[str]:
    tags = _get_tags(config, profile)
    return list(tags.get(key, []))


def find_by_tag(config: Config, profile: str, tag: str) -> List[str]:
    tags = _get_tags(config, profile)
    return [k for k, v in tags.items() if tag in v]
