"""CLI commands for pinning/unpinning keys."""

import click
from envctl.config import Config
from envctl.pin import PinError, pin_key, unpin_key, list_pins


@click.group("pin")
def pin_group():
    """Pin keys to protect them from sync overwrites."""


@pin_group.command("add")
@click.argument("key")
@click.option("--profile", default=None, help="Profile name (default: active).")
@click.pass_context
def add_cmd(ctx, key, profile):
    """Pin KEY in a profile."""
    config: Config = ctx.obj["config"]
    profile = profile or config.get_active_env()
    try:
        added = pin_key(config, profile, key)
        if added:
            click.echo(f"Pinned '{key}' in profile '{profile}'.")
        else:
            click.echo(f"'{key}' is already pinned in '{profile}'.")
    except PinError as e:
        raise click.ClickException(str(e))


@pin_group.command("remove")
@click.argument("key")
@click.option("--profile", default=None, help="Profile name (default: active).")
@click.pass_context
def remove_cmd(ctx, key, profile):
    """Unpin KEY in a profile."""
    config: Config = ctx.obj["config"]
    profile = profile or config.get_active_env()
    try:
        removed = unpin_key(config, profile, key)
        if removed:
            click.echo(f"Unpinned '{key}' from profile '{profile}'.")
        else:
            click.echo(f"'{key}' was not pinned in '{profile}'.")
    except PinError as e:
        raise click.ClickException(str(e))


@pin_group.command("list")
@click.option("--profile", default=None, help="Profile name (default: active).")
@click.pass_context
def list_cmd(ctx, profile):
    """List all pinned keys in a profile."""
    config: Config = ctx.obj["config"]
    profile = profile or config.get_active_env()
    try:
        pins = list_pins(config, profile)
        if not pins:
            click.echo(f"No pinned keys in '{profile}'.")
        else:
            click.echo(f"Pinned keys in '{profile}':")
            for k in pins:
                click.echo(f"  {k}")
    except PinError as e:
        raise click.ClickException(str(e))
