"""CLI commands for rollback."""
import click
from envctl.config import Config
from envctl.rollback import rollback_profile, RollbackError


@click.group("rollback")
def rollback_group():
    """Rollback a profile to a previous snapshot."""


@rollback_group.command("apply")
@click.argument("profile")
@click.argument("snapshot_id")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying.")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def apply_cmd(profile: str, snapshot_id: str, dry_run: bool, config_path: str):
    """Rollback PROFILE to SNAPSHOT_ID."""
    cfg = Config(config_path)
    try:
        diff = rollback_profile(cfg, profile, snapshot_id, dry_run=dry_run)
    except RollbackError as exc:
        raise click.ClickException(str(exc))

    prefix = "[dry-run] " if dry_run else ""
    if not any(diff.values()):
        click.echo(f"{prefix}No changes needed for profile '{profile}'.")
        return

    for key in diff["added"]:
        click.echo(f"{prefix}ADD    {key}={diff['added'][key]}")
    for key in diff["changed"]:
        click.echo(f"{prefix}CHANGE {key}={diff['changed'][key]}")
    for key in diff["removed"]:
        click.echo(f"{prefix}REMOVE {key}")

    if not dry_run:
        click.echo(f"Rolled back '{profile}' to snapshot '{snapshot_id}'.")
