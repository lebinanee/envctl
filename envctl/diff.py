"""diff.py — Generate a human-readable diff report between two environment profiles."""

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.config import Config


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffEntry:
    key: str
    status: str          # 'added' | 'removed' | 'changed' | 'unchanged'
    left_value: Optional[str] = None
    right_value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == "added":
            return f"+ {self.key}={self.right_value}"
        if self.status == "removed":
            return f"- {self.key}={self.left_value}"
        if self.status == "changed":
            return f"~ {self.key}: {self.left_value!r} -> {self.right_value!r}"
        return f"  {self.key}={self.left_value}"


@dataclass
class DiffResult:
    left: str
    right: str
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(e.status != "unchanged" for e in self.entries)

    @property
    def summary(self) -> str:
        added = sum(1 for e in self.entries if e.status == "added")
        removed = sum(1 for e in self.entries if e.status == "removed")
        changed = sum(1 for e in self.entries if e.status == "changed")
        return f"+{added} -{removed} ~{changed}"


def diff_profiles(
    config: Config,
    left: str,
    right: str,
    show_unchanged: bool = False,
) -> DiffResult:
    """Compare two profiles and return a DiffResult."""
    valid = {"local", "staging", "production"}
    if left not in valid:
        raise DiffError(f"Unknown profile: {left!r}")
    if right not in valid:
        raise DiffError(f"Unknown profile: {right!r}")

    left_vars: dict = config.get_profile(left) or {}
    right_vars: dict = config.get_profile(right) or {}

    all_keys = sorted(set(left_vars) | set(right_vars))
    entries: List[DiffEntry] = []

    for key in all_keys:
        in_left = key in left_vars
        in_right = key in right_vars
        if in_left and in_right:
            lv, rv = left_vars[key], right_vars[key]
            if lv == rv:
                if show_unchanged:
                    entries.append(DiffEntry(key, "unchanged", lv, rv))
            else:
                entries.append(DiffEntry(key, "changed", lv, rv))
        elif in_left:
            entries.append(DiffEntry(key, "removed", left_vars[key], None))
        else:
            entries.append(DiffEntry(key, "added", None, right_vars[key]))

    return DiffResult(left=left, right=right, entries=entries)


def format_diff(result: DiffResult) -> str:
    """Render a DiffResult as a printable string."""
    lines = [f"diff {result.left} -> {result.right}  ({result.summary})"]
    if not result.entries:
        lines.append("  (no entries)")
    else:
        for entry in result.entries:
            lines.append(str(entry))
    return "\n".join(lines)
