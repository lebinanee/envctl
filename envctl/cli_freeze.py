"""CLI commands for freeze/unfreeze profile management."""

from __future__ import annotations

import click

from envctl.config import Config
from envctl.freeze import (
    FreezeError,
    freeze_profile,
    unfreeze_profile,
    is_frozen,
    list_frozen,
)


@click.group("freeze")
def freeze_group():
    """Freeze profiles to prevent modifications."""


@freeze_group.command("add")
@click.argument("profile")
def add_cmd(profile: str):
    """Freeze PROFILE to prevent any modifications."""
    config = Config()
    try:
        newly_frozen = freeze_profile(config, profile)
    except FreezeError as exc:
        raise click.ClickException(str(exc))
    if newly_frozen:
        click.echo(f"Profile '{profile}' is now frozen.")
    else:
        click.echo(f"Profile '{profile}' was already frozen.")


@freeze_group.command("remove")
@click.argument("profile")
def remove_cmd(profile: str):
    """Unfreeze PROFILE to allow modifications."""
    config = Config()
    unfrozen = unfreeze_profile(config, profile)
    if unfrozen:
        click.echo(f"Profile '{profile}' has been unfrozen.")
    else:
        click.echo(f"Profile '{profile}' was not frozen.")


@freeze_group.command("status")
@click.argument("profile")
def status_cmd(profile: str):
    """Show freeze status of PROFILE."""
    config = Config()
    frozen = is_frozen(config, profile)
    state = "frozen" if frozen else "not frozen"
    click.echo(f"Profile '{profile}' is {state}.")


@freeze_group.command("list")
def list_cmd():
    """List all frozen profiles."""
    config = Config()
    profiles = list_frozen(config)
    if not profiles:
        click.echo("No profiles are currently frozen.")
        return
    for profile in profiles:
        click.echo(f"  {profile}")
