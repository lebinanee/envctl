"""CLI commands for profile locking."""
import click

from envctl.config import Config
from envctl.lock import LockError, lock_profile, unlock_profile, is_locked, list_locked


@click.group("lock", help="Lock or unlock profiles to prevent accidental writes.")
def lock_group():
    pass


@lock_group.command("add", help="Lock a profile.")
@click.argument("profile")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def add_cmd(profile: str, config_path: str):
    cfg = Config(config_path)
    try:
        added = lock_profile(cfg, profile)
    except LockError as exc:
        raise click.ClickException(str(exc))
    if added:
        click.echo(f"Locked profile '{profile}'.")
    else:
        click.echo(f"Profile '{profile}' is already locked.")


@lock_group.command("remove", help="Unlock a profile.")
@click.argument("profile")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def remove_cmd(profile: str, config_path: str):
    cfg = Config(config_path)
    try:
        removed = unlock_profile(cfg, profile)
    except LockError as exc:
        raise click.ClickException(str(exc))
    if removed:
        click.echo(f"Unlocked profile '{profile}'.")
    else:
        click.echo(f"Profile '{profile}' was not locked.")


@lock_group.command("status", help="Show whether a profile is locked.")
@click.argument("profile")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def status_cmd(profile: str, config_path: str):
    cfg = Config(config_path)
    locked = is_locked(cfg, profile)
    state = "locked" if locked else "unlocked"
    click.echo(f"Profile '{profile}' is {state}.")


@lock_group.command("list", help="List all locked profiles.")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def list_cmd(config_path: str):
    cfg = Config(config_path)
    locked = list_locked(cfg)
    if not locked:
        click.echo("No profiles are locked.")
    else:
        for name in locked:
            click.echo(name)
