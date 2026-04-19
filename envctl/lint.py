"""Lint environment variable profiles for common issues."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from envctl.config import Config


class LintError(Exception):
    pass


@dataclass
class LintIssue:
    profile: str
    key: str
    severity: str  # 'warning' | 'error'
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.profile}/{self.key}: {self.message}"


DEFAULT_SUSPICIOUS_PATTERNS = ["TODO", "FIXME", "CHANGEME", "PLACEHOLDER"]


def lint_profile(
    config: Config,
    profile: str,
    suspicious: Optional[List[str]] = None,
) -> List[LintIssue]:
    data = config.data.get("profiles", {}).get(profile)
    if data is None:
        raise LintError(f"Profile '{profile}' not found.")

    patterns = suspicious if suspicious is not None else DEFAULT_SUSPICIOUS_PATTERNS
    issues: List[LintIssue] = []

    for key, value in data.items():
        if not value or not str(value).strip():
            issues.append(LintIssue(profile, key, "error", "Value is empty or blank."))
            continue

        val_str = str(value)

        for pat in patterns:
            if pat.lower() in val_str.lower():
                issues.append(
                    LintIssue(profile, key, "warning", f"Value contains suspicious pattern '{pat}'.")
                )

        if len(val_str) > 500:
            issues.append(LintIssue(profile, key, "warning", "Value is unusually long (>500 chars)."))

        if " " in key:
            issues.append(LintIssue(profile, key, "error", "Key contains whitespace."))

    return issues


def lint_all_profiles(config: Config) -> dict[str, List[LintIssue]]:
    profiles = config.data.get("profiles", {})
    return {profile: lint_profile(config, profile) for profile in profiles}
