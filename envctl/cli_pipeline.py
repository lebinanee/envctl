"""CLI commands for the pipeline feature."""
from __future__ import annotations

import click

from envctl.config import Config
from envctl.pipeline import (
    PipelineError,
    PipelineStep,
    build_pipeline,
    run_pipeline,
)


@click.group("pipeline")
def pipeline_group() -> None:
    """Chain and apply env-var transform pipelines."""


# ---------------------------------------------------------------------------
# Built-in transform helpers exposed via CLI
# ---------------------------------------------------------------------------

def _make_uppercase_step() -> PipelineStep:
    return PipelineStep(
        name="uppercase-values",
        fn=lambda v: {k: val.upper() if isinstance(val, str) else val for k, val in v.items()},
        description="Convert all values to uppercase",
    )


def _make_strip_step() -> PipelineStep:
    return PipelineStep(
        name="strip-whitespace",
        fn=lambda v: {k: val.strip() if isinstance(val, str) else val for k, val in v.items()},
        description="Strip leading/trailing whitespace from values",
    )


def _make_prefix_step(prefix: str) -> PipelineStep:
    return PipelineStep(
        name=f"prefix-keys:{prefix}",
        fn=lambda v, p=prefix: {f"{p}{k}" if not k.startswith(p) else k: val for k, val in v.items()},
        description=f"Prefix all keys with '{prefix}'",
    )


_BUILTIN_STEPS = {
    "uppercase-values": _make_uppercase_step,
    "strip-whitespace": _make_strip_step,
}


@pipeline_group.command("run")
@click.argument("profile")
@click.option("--step", "steps", multiple=True, required=True, help="Step name(s) to apply in order.")
@click.option("--prefix", default=None, help="Key prefix to apply (adds prefix-keys step).")
@click.option("--dry-run", is_flag=True, help="Preview changes without saving.")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def run_cmd(
    profile: str,
    steps: tuple,
    prefix: str | None,
    dry_run: bool,
    config_path: str,
) -> None:
    """Apply a named sequence of transforms to PROFILE."""
    cfg = Config(config_path)
    pipeline_steps = []

    for name in steps:
        if name in _BUILTIN_STEPS:
            pipeline_steps.append(_BUILTIN_STEPS[name]())
        else:
            click.echo(f"Unknown step: '{name}'", err=True)
            raise SystemExit(1)

    if prefix:
        pipeline_steps.append(_make_prefix_step(prefix))

    try:
        ordered = build_pipeline(pipeline_steps)
        result = run_pipeline(cfg, profile, ordered, dry_run=dry_run)
    except PipelineError as exc:
        click.echo(f"Pipeline error: {exc}", err=True)
        raise SystemExit(1)

    for name in result.steps_applied:
        click.echo(f"  [ok] {name}")
    for name in result.steps_skipped:
        click.echo(f"  [skip] {name}")

    if dry_run:
        click.echo(f"Dry run — {result.total_applied} step(s) would be applied to '{profile}'.")
    else:
        click.echo(f"Pipeline complete — {result.total_applied} step(s) applied to '{profile}'.")
