"""CLI commands for masking sensitive env var values."""

import click
from envctl.config import Config
from envctl.mask import mask_profile, MaskError


@click.group("mask")
def mask_group():
    """View environment variables with sensitive values masked."""


@mask_group.command("show")
@click.argument("profile")
@click.option("--key", "-k", multiple=True, help="Specific key(s) to show (default: all).")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def show_cmd(profile: str, key: tuple, config_path: str):
    """Show env vars for PROFILE with sensitive values masked."""
    cfg = Config(config_path)
    keys = list(key) if key else None
    try:
        result = mask_profile(cfg, profile, keys)
    except MaskError as e:
        raise click.ClickException(str(e))

    if not result:
        click.echo(f"No variables found in profile '{profile}'.")
        return

    max_len = max(len(k) for k in result)
    for k, v in sorted(result.items()):
        click.echo(f"  {k:<{max_len}}  =  {v}")
