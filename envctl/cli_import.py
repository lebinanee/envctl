"""CLI commands for importing .env files into envctl profiles."""

import click
from envctl.config import Config
from envctl.import_ import import_into_profile, ImportError as EnvImportError


@click.group("import")
def import_group():
    """Import variables from .env files."""


@import_group.command("file")
@click.argument("env")
@click.argument("path")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without saving.")
@click.option("--config", "config_path", default=None, help="Path to config file.")
def import_cmd(env, path, overwrite, dry_run, config_path):
    """Import variables from a .env FILE into ENV profile."""
    try:
        cfg = Config(config_path)
        summary = import_into_profile(cfg, env, path, overwrite=overwrite, dry_run=dry_run)
    except EnvImportError as e:
        raise click.ClickException(str(e))

    prefix = "[dry-run] " if dry_run else ""
    if summary["added"]:
        click.echo(f"{prefix}Added: {', '.join(summary['added'])}")
    if summary["updated"]:
        click.echo(f"{prefix}Updated: {', '.join(summary['updated'])}")
    if summary["skipped"]:
        click.echo(f"{prefix}Skipped (already exist): {', '.join(summary['skipped'])}")
    if not any(summary.values()):
        click.echo(f"{prefix}No variables imported.")
