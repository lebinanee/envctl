"""CLI commands for the dedupe feature."""

from __future__ import annotations

import click

from envctl.config import Config
from envctl.dedupe import DedupeError, dedupe_profile


@click.group("dedupe")
def dedupe_group() -> None:
    """Find and remove duplicate values within a profile."""


@dedupe_group.command("apply")
@click.argument("profile")
@click.option("--keys", "-k", multiple=True, help="Limit to specific keys.")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be removed without making changes.",
)
@click.pass_context
def apply_cmd(ctx: click.Context, profile: str, keys: tuple, dry_run: bool) -> None:
    """Remove keys with duplicate values in PROFILE."""
    cfg: Config = ctx.obj["config"]
    try:
        result = dedupe_profile(
            cfg,
            profile,
            keys=list(keys) if keys else None,
            dry_run=dry_run,
        )
    except DedupeError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.removed:
        click.echo("No duplicate values found.")
        return

    label = "Would remove" if dry_run else "Removed"
    for key in result.removed:
        click.echo(f"  {label}: {key}")

    summary = f"{label} {result.total_removed} duplicate key(s) from '{profile}'."
    if dry_run:
        summary += " (dry run — no changes written)"
    click.echo(summary)
