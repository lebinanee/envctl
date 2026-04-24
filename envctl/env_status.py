"""env_status.py — Summarise health and completeness of an environment profile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.config import Config
from envctl.lint import lint_profile, LintIssue
from envctl.schema import get_schema, validate_profile as schema_validate, SchemaViolation


class StatusError(Exception):
    """Raised when the status check cannot be completed."""


@dataclass
class ProfileStatus:
    profile: str
    total_keys: int
    empty_keys: List[str] = field(default_factory=list)
    lint_issues: List[LintIssue] = field(default_factory=list)
    schema_violations: List[SchemaViolation] = field(default_factory=list)
    missing_schema_keys: List[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        errors = [i for i in self.lint_issues if i.level == "error"]
        return (
            not errors
            and not self.schema_violations
            and not self.missing_schema_keys
        )

    def summary(self) -> str:
        lines = [
            f"Profile : {self.profile}",
            f"Keys    : {self.total_keys}",
            f"Empty   : {len(self.empty_keys)}",
            f"Lint    : {len(self.lint_issues)} issue(s)",
            f"Schema  : {len(self.schema_violations)} violation(s), "
            f"{len(self.missing_schema_keys)} missing required key(s)",
            f"Healthy : {'yes' if self.healthy else 'NO'}",
        ]
        return "\n".join(lines)


def profile_status(
    config: Config,
    profile: str,
    schema_path: Optional[str] = None,
) -> ProfileStatus:
    """Return a :class:`ProfileStatus` for *profile*."""
    env_vars = config.get_profile(profile)
    if env_vars is None:
        raise StatusError(f"Profile '{profile}' does not exist.")

    empty_keys = [k for k, v in env_vars.items() if not v or not v.strip()]

    try:
        lint_issues = lint_profile(config, profile)
    except Exception:
        lint_issues = []

    violations: List[SchemaViolation] = []
    missing: List[str] = []
    if schema_path:
        schema = get_schema(schema_path)
        if schema:
            result = schema_validate(env_vars, schema)
            violations = result.violations
            missing = result.missing_required

    return ProfileStatus(
        profile=profile,
        total_keys=len(env_vars),
        empty_keys=empty_keys,
        lint_issues=lint_issues,
        schema_violations=violations,
        missing_schema_keys=missing,
    )
