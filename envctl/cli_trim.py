"""CLI commands for the trim feature."""

from __future__ import annotations

from typing import Optional, Tuple

import click

from envctl.config import Config
from envctl.trim import TrimError, trim_profile


@click.group(name="trim")
def trim_group() -> None:
    """Trim whitespace from environment variable values."""


@trim_group.command(name="apply")
@click.argument("profile")
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Specific key(s) to trim. Trims all keys if omitted.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without saving.",
)
@click.pass_context
def apply_cmd(
    ctx: click.Context,
    profile: str,
    keys: Tuple[str, ...],
    dry_run: bool,
) -> None:
    """Trim leading/trailing whitespace from values in PROFILE."""
    config: Config = ctx.obj["config"]
    try:
        result = trim_profile(
            config,
            profile,
            keys=list(keys) if keys else None,
            dry_run=dry_run,
        )
    except TrimError as exc:
        raise click.ClickException(str(exc)) from exc

    if dry_run:
        click.echo("[dry-run] No changes written.")

    if result.total_trimmed == 0:
        click.echo("No values required trimming.")
        return

    for key in result.trimmed:
        click.echo(f"  trimmed: {key}")

    click.echo(
        f"\nDone. {result.total_trimmed} trimmed, {result.total_skipped} unchanged."
    )
