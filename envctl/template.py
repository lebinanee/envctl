"""Template rendering: substitute env vars into a template string."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from envctl.config import Config

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Z_][A-Z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    pass


@dataclass
class RenderResult:
    output: str
    resolved: list[str]
    missing: list[str]


def render_template(
    template: str,
    config: Config,
    profile: Optional[str] = None,
    strict: bool = False,
) -> RenderResult:
    """Replace {{KEY}} placeholders with values from the given profile.

    Args:
        template: Raw template string.
        config: Config instance to read values from.
        profile: Profile name; defaults to the active env.
        strict: If True, raise TemplateError on missing keys.

    Returns:
        RenderResult with the rendered output and resolution metadata.
    """
    env = profile or config.get_active_env()
    data: dict = config.get_profile(env) or {}

    resolved: list[str] = []
    missing: list[str] = []

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in data:
            resolved.append(key)
            return data[key]
        missing.append(key)
        if strict:
            raise TemplateError(
                f"Key '{key}' not found in profile '{env}'"
            )
        return match.group(0)

    output = _PLACEHOLDER.sub(replacer, template)
    return RenderResult(output=output, resolved=resolved, missing=missing)
