"""CLI commands for the transform feature."""
import click

from envctl.config import Config
from envctl.transform import TransformError, transform_profile


@click.group("transform")
def transform_group():
    """Apply value transformations to a profile."""


@transform_group.command("apply")
@click.argument("profile")
@click.argument("transform", metavar="TRANSFORM")
@click.option("--key", "keys", multiple=True, help="Limit to specific keys.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without saving.")
@click.option("--config", "config_path", default=None, hidden=True)
def apply_cmd(profile, transform, keys, dry_run, config_path):
    """Apply TRANSFORM to all values in PROFILE.

    Available transforms: upper, lower, strip, trim_quotes
    """
    cfg = Config(config_path)
    try:
        result = transform_profile(
            cfg,
            profile,
            transform,
            keys=list(keys) if keys else None,
            dry_run=dry_run,
        )
    except TransformError as exc:
        raise click.ClickException(str(exc))

    if not result.applied:
        click.echo("No changes to apply.")
        return

    prefix = "[dry-run] " if dry_run else ""
    for key, new_val in result.applied.items():
        click.echo(f"{prefix}  {key} -> {new_val}")

    if dry_run:
        click.echo(f"\n{prefix}{result.total_applied} key(s) would be updated.")
    else:
        click.echo(f"\nApplied '{transform}' to {result.total_applied} key(s) in '{profile}'.")

    if result.skipped:
        click.echo(f"Skipped {len(result.skipped)} unchanged key(s).")
