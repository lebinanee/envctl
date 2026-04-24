"""CLI commands for profile inheritance."""

from __future__ import annotations

import click

from envctl.config import Config
from envctl.inherit import InheritError, inherit_profile


@click.group("inherit")
def inherit_group() -> None:
    """Inherit variables from a base profile into a child profile."""


@inherit_group.command("apply")
@click.argument("base")
@click.argument("child")
@click.option("--key", "keys", multiple=True, help="Specific key(s) to inherit.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in child.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without applying them.")
@click.option("--config", "config_path", default=None, help="Path to config file.")
def apply_cmd(
    base: str,
    child: str,
    keys: tuple,
    overwrite: bool,
    dry_run: bool,
    config_path: str | None,
) -> None:
    """Inherit variables from BASE profile into CHILD profile."""
    cfg = Config(path=config_path)
    try:
        result = inherit_profile(
            cfg,
            base=base,
            child=child,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
            dry_run=dry_run,
        )
    except InheritError as exc:
        raise click.ClickException(str(exc)) from exc

    prefix = "[dry-run] " if dry_run else ""

    if result.inherited:
        click.echo(f"{prefix}Inherited ({len(result.inherited)}): {', '.join(result.inherited)}")
    if result.overwritten:
        click.echo(f"{prefix}Overwritten ({len(result.overwritten)}): {', '.join(result.overwritten)}")
    if result.skipped:
        click.echo(f"Skipped (already exist, {len(result.skipped)}): {', '.join(result.skipped)}")

    if result.total_changes == 0 and not result.skipped:
        click.echo("Nothing to inherit.")
    elif result.total_changes == 0:
        click.echo("No new keys inherited.")
    else:
        action = "Would inherit" if dry_run else "Inherited"
        click.echo(f"{action} {result.total_changes} key(s) from '{base}' into '{child}'.")
