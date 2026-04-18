"""CLI commands for renaming keys."""

from __future__ import annotations
import click
from envctl.config import Config
from envctl.rename import rename_key, RenameError
from envctl.validate import ValidationError


@click.group("rename")
def rename_group() -> None:
    """Rename keys in environment profiles."""


@rename_group.command("key")
@click.argument("old_key")
@click.argument("new_key")
@click.option("--profile", "-p", default=None, help="Limit to a single profile.")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def rename_cmd(
    old_key: str,
    new_key: str,
    profile: str | None,
    config_path: str,
) -> None:
    """Rename OLD_KEY to NEW_KEY across profiles."""
    try:
        cfg = Config(config_path)
        results = rename_key(cfg, old_key, new_key, profile)
    except (RenameError, ValidationError) as exc:
        raise click.ClickException(str(exc))

    renamed = [p for p, ok in results.items() if ok]
    skipped = [p for p, ok in results.items() if not ok]

    if renamed:
        click.echo(f"Renamed '{old_key}' -> '{new_key}' in: {', '.join(renamed)}")
    if skipped:
        click.echo(f"Key '{old_key}' not found in: {', '.join(skipped)}")
    if not renamed:
        raise click.ClickException(f"Key '{old_key}' was not found in any profile.")
