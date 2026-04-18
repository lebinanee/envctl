"""Compare environment profiles and produce human-readable reports."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from envctl.config import Config


class CompareError(Exception):
    pass


@dataclass
class CompareEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'same'
    source_value: Optional[str] = None
    target_value: Optional[str] = None


def compare_profiles(
    config: Config,
    source: str,
    target: str,
    keys: Optional[List[str]] = None,
    only_diff: bool = False,
) -> List[CompareEntry]:
    """Compare two profiles and return a list of CompareEntry results."""
    src = config.get_profile(source)
    tgt = config.get_profile(target)

    if src is None:
        raise CompareError(f"Source profile '{source}' not found.")
    if tgt is None:
        raise CompareError(f"Target profile '{target}' not found.")

    all_keys = set(src) | set(tgt)
    if keys:
        all_keys = all_keys & set(keys)

    results: List[CompareEntry] = []
    for key in sorted(all_keys):
        sv = src.get(key)
        tv = tgt.get(key)
        if sv is None:
            status = "added"
        elif tv is None:
            status = "removed"
        elif sv != tv:
            status = "changed"
        else:
            status = "same"

        if only_diff and status == "same":
            continue

        results.append(CompareEntry(key=key, status=status, source_value=sv, target_value=tv))

    return results


def format_report(entries: List[CompareEntry], source: str, target: str) -> str:
    """Format compare entries into a readable string report."""
    lines = [f"Comparing '{source}' → '{target}':"]
    if not entries:
        lines.append("  (no differences)")
        return "\n".join(lines)
    for e in entries:
        if e.status == "added":
            lines.append(f"  + {e.key} = {e.target_value}")
        elif e.status == "removed":
            lines.append(f"  - {e.key} = {e.source_value}")
        elif e.status == "changed":
            lines.append(f"  ~ {e.key}: {e.source_value!r} → {e.target_value!r}")
        else:
            lines.append(f"    {e.key} = {e.source_value}")
    return "\n".join(lines)
