"""CLI commands for pruning empty/whitespace keys from profiles."""

from __future__ import annotations

import click

from envctl.config import Config
from envctl.prune import PruneError, prune_profile


@click.group("prune")
def prune_group() -> None:
    """Prune empty or whitespace-only keys from a profile."""


@prune_group.command("apply")
@click.argument("profile")
@click.option("--key", "keys", multiple=True, help="Limit pruning to specific keys.")
@click.option(
    "--no-empty",
    "remove_empty",
    is_flag=True,
    default=True,
    show_default=True,
    help="Remove keys with empty string values.",
)
@click.option(
    "--no-whitespace",
    "remove_whitespace_only",
    is_flag=True,
    default=True,
    show_default=True,
    help="Remove keys with whitespace-only values.",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without applying them.")
@click.pass_context
def apply_cmd(
    ctx: click.Context,
    profile: str,
    keys: tuple,
    remove_empty: bool,
    remove_whitespace_only: bool,
    dry_run: bool,
) -> None:
    """Remove empty/whitespace keys from PROFILE."""
    config: Config = ctx.obj
    try:
        result = prune_profile(
            config,
            profile,
            remove_empty=remove_empty,
            remove_whitespace_only=remove_whitespace_only,
            keys=list(keys) if keys else None,
            dry_run=dry_run,
        )
    except PruneError as exc:
        raise click.ClickException(str(exc)) from exc

    if dry_run:
        click.echo("[dry-run] No changes written.")

    if result.removed:
        for key in result.removed:
            click.echo(f"  {'would remove' if dry_run else 'removed'}: {key}")
    else:
        click.echo("Nothing to prune.")

    click.echo(
        f"\nSummary: {result.total_removed} removed, {result.total_skipped} skipped."
    )
