"""CLI commands for sync and export features."""

import click
from envctl.config import Config
from envctl.sync import sync_envs, SyncError, ENVIRONMENTS
from envctl.export import export_to_file, render, ExportError


@click.group()
def sync_group():
    """Sync and export environment variable commands."""


@sync_group.command("sync")
@click.argument("source", type=click.Choice(ENVIRONMENTS))
@click.argument("target", type=click.Choice(ENVIRONMENTS))
@click.option("--keys", "-k", multiple=True, help="Specific keys to sync.")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying.")
@click.pass_context
def sync_cmd(ctx, source, target, keys, dry_run):
    """Sync variables from SOURCE to TARGET environment."""
    cfg: Config = ctx.obj
    try:
        changes = sync_envs(cfg, source, target, keys=list(keys) or None, dry_run=dry_run)
    except SyncError as exc:
        raise click.ClickException(str(exc))

    prefix = "[dry-run] " if dry_run else ""
    if changes["added"]:
        click.echo(f"{prefix}Added: {list(changes['added'].keys())}")
    if changes["changed"]:
        click.echo(f"{prefix}Changed: {list(changes['changed'].keys())}")
    if changes["removed"]:
        click.echo(f"{prefix}Would remove (not applied): {list(changes['removed'].keys())}")
    if not any(changes.values()):
        click.echo(f"{prefix}No differences found.")
    elif not dry_run:
        click.echo(f"Synced '{source}' → '{target}'.")


@sync_group.command("export")
@click.argument("env", type=click.Choice(ENVIRONMENTS))
@click.option("--format", "fmt", default="dotenv", show_default=True,
              type=click.Choice(["dotenv", "shell"]), help="Output format.")
@click.option("--output", "-o", default=None, help="Output file path (prints to stdout if omitted).")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file.")
@click.pass_context
def export_cmd(ctx, env, fmt, output, overwrite):
    """Export variables for ENV to a file or stdout."""
    cfg: Config = ctx.obj
    if output:
        try:
            export_to_file(cfg, env, output, fmt=fmt, overwrite=overwrite)
        except ExportError as exc:
            raise click.ClickException(str(exc))
        click.echo(f"Exported '{env}' to '{output}' ({fmt} format).")
    else:
        variables = cfg.get_profile(env) or {}
        click.echo(render(variables, fmt=fmt), nl=False)
