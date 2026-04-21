"""CLI commands for TTL management."""
import click
from envctl.config import Config
from envctl import ttl as ttl_mod


@click.group(name="ttl")
def ttl_group():
    """Manage key TTLs (time-to-live)."""


@ttl_group.command(name="set")
@click.argument("profile")
@click.argument("key")
@click.option("--seconds", "-s", type=int, required=True, help="TTL in seconds")
@click.pass_context
def set_cmd(ctx, profile: str, key: str, seconds: int):
    """Set a TTL on a key in a profile."""
    cfg = Config()
    try:
        entry = ttl_mod.set_ttl(cfg, profile, key, seconds)
        click.echo(f"TTL set: {key} in '{profile}' expires at {entry.expires_at} (UTC)")
    except ttl_mod.TTLError as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)


@ttl_group.command(name="get")
@click.argument("profile")
@click.argument("key")
def get_cmd(profile: str, key: str):
    """Show the TTL for a specific key."""
    cfg = Config()
    entry = ttl_mod.get_ttl(cfg, profile, key)
    if entry is None:
        click.echo(f"No TTL set for '{key}' in profile '{profile}'.")
    else:
        status = "EXPIRED" if entry.is_expired() else "active"
        click.echo(f"{key}: expires_at={entry.expires_at} [{status}]")


@ttl_group.command(name="list")
@click.argument("profile")
def list_cmd(profile: str):
    """List all TTL entries for a profile."""
    cfg = Config()
    entries = ttl_mod.list_ttls(cfg, profile)
    if not entries:
        click.echo(f"No TTLs set for profile '{profile}'.")
        return
    for e in entries:
        status = "EXPIRED" if e.is_expired() else "active"
        click.echo(f"  {e.key}: {e.expires_at} [{status}]")


@ttl_group.command(name="purge")
@click.argument("profile")
def purge_cmd(profile: str):
    """Remove all expired keys from a profile."""
    cfg = Config()
    removed = ttl_mod.purge_expired(cfg, profile)
    if not removed:
        click.echo("No expired keys found.")
    else:
        for k in removed:
            click.echo(f"Removed expired key: {k}")
