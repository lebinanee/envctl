"""Pipeline: chain multiple env transforms and apply them in sequence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from envctl.config import Config


class PipelineError(Exception):
    """Raised when a pipeline step fails."""


@dataclass
class PipelineStep:
    name: str
    fn: Callable[[dict], dict]
    description: str = ""


@dataclass
class PipelineResult:
    profile: str
    steps_applied: List[str] = field(default_factory=list)
    steps_skipped: List[str] = field(default_factory=list)
    final_vars: dict = field(default_factory=dict)

    @property
    def total_applied(self) -> int:
        return len(self.steps_applied)


def build_pipeline(steps: List[PipelineStep]) -> List[PipelineStep]:
    """Validate and return the ordered list of pipeline steps."""
    seen = set()
    for step in steps:
        if step.name in seen:
            raise PipelineError(f"Duplicate step name: '{step.name}'")
        seen.add(step.name)
    return list(steps)


def run_pipeline(
    cfg: Config,
    profile: str,
    steps: List[PipelineStep],
    dry_run: bool = False,
    stop_on_error: bool = True,
) -> PipelineResult:
    """Run each step in sequence against the profile's vars."""
    vars_ = cfg.get_profile(profile)
    if vars_ is None:
        raise PipelineError(f"Profile '{profile}' not found.")

    current = dict(vars_)
    result = PipelineResult(profile=profile)

    for step in steps:
        try:
            transformed = step.fn(dict(current))
            if not isinstance(transformed, dict):
                raise PipelineError(
                    f"Step '{step.name}' must return a dict, got {type(transformed).__name__}"
                )
            current = transformed
            result.steps_applied.append(step.name)
        except PipelineError:
            raise
        except Exception as exc:  # noqa: BLE001
            if stop_on_error:
                raise PipelineError(f"Step '{step.name}' raised: {exc}") from exc
            result.steps_skipped.append(step.name)

    result.final_vars = current

    if not dry_run:
        cfg.set_profile(profile, current)
        cfg.save()

    return result
