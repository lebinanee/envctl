"""CLI commands for the normalize feature."""
from __future__ import annotations

import click

from envctl.config import Config
from envctl.normalize import NormalizeError, normalize_profile


@click.group("normalize")
def normalize_group():
    """Normalize environment variable values."""


@normalize_group.command("apply")
@click.argument("profile")
@click.option(
    "--strategy",
    "-s",
    default="strip",
    show_default=True,
    type=click.Choice(["upper", "lower", "strip", "title"], case_sensitive=False),
    help="Normalization strategy to apply.",
)
@click.option("--key", "-k", "keys", multiple=True, help="Restrict to specific keys.")
@click.option("--dry-run", is_flag=True, help="Preview changes without saving.")
@click.pass_context
def apply_cmd(ctx, profile: str, strategy: str, keys, dry_run: bool):
    """Apply a normalization strategy to values in PROFILE."""
    cfg: Config = ctx.obj["config"]
    try:
        result = normalize_profile(
            cfg,
            profile,
            strategy=strategy.lower(),
            keys=list(keys) or None,
            dry_run=dry_run,
        )
    except NormalizeError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.applied and not result.skipped:
        click.echo("Nothing to normalize.")
        return

    prefix = "[dry-run] " if dry_run else ""
    for key, new_val in result.applied.items():
        click.echo(f"{prefix}  normalized  {key} -> {new_val!r}")
    for key, reason in result.skipped.items():
        click.echo(f"  skipped     {key} ({reason})")

    click.echo(
        f"\n{prefix}Applied {result.total_applied}, "
        f"skipped {result.total_skipped} key(s) in '{profile}'."
    )
