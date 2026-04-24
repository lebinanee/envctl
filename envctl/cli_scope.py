"""CLI commands for scope management."""

from __future__ import annotations

import click

from envctl.config import Config
from envctl.scope import ScopeError, apply_scope, get_scope, list_scopes, set_scope


@click.group("scope")
def scope_group() -> None:
    """Manage key scopes per environment profile."""


@scope_group.command("set")
@click.argument("profile")
@click.argument("keys", nargs=-1, required=True)
@click.option("--config", "config_path", default=".envctl.json", show_default=True)
def set_cmd(profile: str, keys: tuple, config_path: str) -> None:
    """Set the allowed key scope for PROFILE."""
    cfg = Config(config_path)
    try:
        set_scope(cfg.config_dir, profile, list(keys))
        click.echo(f"Scope set for '{profile}': {', '.join(sorted(keys))}")
    except ScopeError as exc:
        raise click.ClickException(str(exc))


@scope_group.command("clear")
@click.argument("profile")
@click.option("--config", "config_path", default=".envctl.json", show_default=True)
def clear_cmd(profile: str, config_path: str) -> None:
    """Clear the scope restriction for PROFILE."""
    cfg = Config(config_path)
    try:
        set_scope(cfg.config_dir, profile, [])
        click.echo(f"Scope cleared for '{profile}'.")
    except ScopeError as exc:
        raise click.ClickException(str(exc))


@scope_group.command("show")
@click.argument("profile")
@click.option("--config", "config_path", default=".envctl.json", show_default=True)
def show_cmd(profile: str, config_path: str) -> None:
    """Show the active scope for PROFILE."""
    cfg = Config(config_path)
    scope = get_scope(cfg.config_dir, profile)
    if scope is None:
        click.echo(f"No scope defined for '{profile}' (all keys visible).")
    else:
        click.echo(f"Scope for '{profile}':")
        for key in scope:
            click.echo(f"  {key}")


@scope_group.command("list")
@click.option("--config", "config_path", default=".envctl.json", show_default=True)
def list_cmd(config_path: str) -> None:
    """List all defined scopes."""
    cfg = Config(config_path)
    scopes = list_scopes(cfg.config_dir)
    if not scopes:
        click.echo("No scopes defined.")
        return
    for profile, keys in sorted(scopes.items()):
        click.echo(f"{profile}: {', '.join(keys)}")


@scope_group.command("apply")
@click.argument("profile")
@click.option("--config", "config_path", default=".envctl.json", show_default=True)
def apply_cmd(profile: str, config_path: str) -> None:
    """Show vars for PROFILE filtered by its scope."""
    cfg = Config(config_path)
    vars_ = cfg.get_profile(profile)
    if vars_ is None:
        raise click.ClickException(f"Profile '{profile}' not found.")
    scope = get_scope(cfg.config_dir, profile)
    filtered = apply_scope(vars_, scope)
    if not filtered:
        click.echo("No variables in scope.")
        return
    for k, v in sorted(filtered.items()):
        click.echo(f"{k}={v}")
