"""Main CLI entry point for envctl."""

import click
from envctl.config import Config
from envctl.cli_sync import sync_group
from envctl.cli_audit import audit_group
from envctl.cli_snapshot import snapshot_group


@click.group()
def cli():
    """envctl — manage and sync environment variables."""


@cli.command()
@click.argument("env")
def use(env: str):
    """Switch the active environment."""
    config = Config()
    try:
        config.set_active_env(env)
        config.save()
        click.echo(f"Switched to environment: {env}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def status():
    """Show current active environment."""
    config = Config()
    click.echo(f"Active environment: {config.get_active_env()}")


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--env", "-e", default=None, help="Target environment (default: active).")
def set_var(key: str, value: str, env):
    """Set a variable in an environment profile."""
    config = Config()
    target = env or config.get_active_env()
    profile = config.get_profile(target) or {}
    profile[key] = value
    config.set_profile(target, profile)
    config.save()
    click.echo(f"Set {key} in [{target}].")


@cli.command("list")
@click.option("--env", "-e", default=None, help="Target environment (default: active).")
def list_vars(env):
    """List variables in an environment profile."""
    config = Config()
    target = env or config.get_active_env()
    profile = config.get_profile(target) or {}
    if not profile:
        click.echo(f"No variables set in [{target}].")
        return
    for k, v in sorted(profile.items()):
        click.echo(f"{k}={v}")


cli.add_command(sync_group, "sync")
cli.add_command(audit_group, "audit")
cli.add_command(snapshot_group, "snapshot")


if __name__ == "__main__":
    cli()
