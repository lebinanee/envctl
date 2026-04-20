"""CLI commands for merging profiles."""

from __future__ import annotations

import click

from envctl.config import Config
from envctl.merge import MergeError, merge_profiles


@click.group("merge")
def merge_group() -> None:
    """Merge variables between profiles."""


@merge_group.command("apply")
@click.argument("src")
@click.argument("dst")
@click.option("--keys", "-k", multiple=True, help="Specific keys to merge.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without applying.")
@click.option("--config", "config_path", default=None, hidden=True)
def apply_cmd(
    src: str,
    dst: str,
    keys: tuple,
    overwrite: bool,
    dry_run: bool,
    config_path: str,
) -> None:
    """Merge variables from SRC profile into DST profile."""
    cfg = Config(path=config_path) if config_path else Config()
    try:
        result = merge_profiles(
            cfg,
            src=src,
            dst=dst,
            keys=list(keys) or None,
            overwrite=overwrite,
            dry_run=dry_run,
        )
    except MergeError as exc:
        raise click.ClickException(str(exc)) from exc

    prefix = "[dry-run] " if dry_run else ""

    if result.added:
        click.echo(f"{prefix}Added ({len(result.added)}): {', '.join(sorted(result.added))}")
    if result.updated:
        click.echo(f"{prefix}Updated ({len(result.updated)}): {', '.join(sorted(result.updated))}")
    if result.skipped:
        click.echo(f"Skipped unchanged ({len(result.skipped)}): {', '.join(sorted(result.skipped))}")
    if result.conflicts:
        click.echo(
            f"Conflicts — use --overwrite to apply ({len(result.conflicts)}): "
            f"{', '.join(sorted(result.conflicts))}",
            err=True,
        )

    if result.total_changes == 0 and not result.conflicts:
        click.echo("Nothing to merge.")
    elif not dry_run and result.total_changes > 0:
        click.echo(f"Merged {result.total_changes} key(s) from '{src}' into '{dst}'.")
