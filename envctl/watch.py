"""Watch a profile for changes and emit diffs."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envctl.config import Config
from envctl.sync import diff_envs


class WatchError(Exception):
    pass


@dataclass
class WatchEvent:
    profile: str
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts: List[str] = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        return ", ".join(parts) if parts else "no changes"


def _snapshot(config: Config, profile: str) -> Dict[str, str]:
    data = config.data.get("profiles", {}).get(profile, {})
    return dict(data)


def watch_profile(
    config: Config,
    profile: str,
    callback: Callable[[WatchEvent], None],
    interval: float = 2.0,
    max_cycles: Optional[int] = None,
) -> None:
    """Poll profile for changes, calling *callback* on each diff."""
    if profile not in config.data.get("profiles", {}):
        raise WatchError(f"Profile '{profile}' not found.")

    previous = _snapshot(config, profile)
    cycles = 0

    while max_cycles is None or cycles < max_cycles:
        time.sleep(interval)
        config._load()
        current = _snapshot(config, profile)
        diffs = diff_envs(previous, current)

        event = WatchEvent(
            profile=profile,
            added=diffs.get("added", {}),
            removed=diffs.get("removed", {}),
            changed=diffs.get("changed", {}),
        )

        if event.has_changes():
            callback(event)

        previous = current
        cycles += 1
