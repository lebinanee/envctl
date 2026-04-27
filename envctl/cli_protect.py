"""CLI commands for the protect feature."""
from __future__ import annotations

import click

from envctl.config import Config
from envctl.protect import (
    ProtectError,
    protect_key,
    unprotect_key,
    is_protected,
    list_protected,
)


@click.group("protect", help="Manage protected (read-only) keys.")
def protect_group():
    pass


@protect_group.command("add", help="Protect a key from modification.")
@click.argument("profile")
@click.argument("key")
@click.pass_context
def add_cmd(ctx, profile: str, key: str):
    config: Config = ctx.obj["config"]
    try:
        added = protect_key(config, profile, key)
    except ProtectError as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)
        return
    if added:
        click.echo(f"Key '{key}' in profile '{profile}' is now protected.")
    else:
        click.echo(f"Key '{key}' in profile '{profile}' was already protected.")


@protect_group.command("remove", help="Remove protection from a key.")
@click.argument("profile")
@click.argument("key")
@click.pass_context
def remove_cmd(ctx, profile: str, key: str):
    config: Config = ctx.obj["config"]
    try:
        removed = unprotect_key(config, profile, key)
    except ProtectError as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)
        return
    if removed:
        click.echo(f"Protection removed from '{key}' in profile '{profile}'.")
    else:
        click.echo(f"Key '{key}' in profile '{profile}' was not protected.")


@protect_group.command("status", help="Check whether a key is protected.")
@click.argument("profile")
@click.argument("key")
@click.pass_context
def status_cmd(ctx, profile: str, key: str):
    config: Config = ctx.obj["config"]
    protected = is_protected(config, profile, key)
    state = "protected" if protected else "not protected"
    click.echo(f"Key '{key}' in profile '{profile}': {state}.")


@protect_group.command("list", help="List all protected keys for a profile.")
@click.argument("profile")
@click.pass_context
def list_cmd(ctx, profile: str):
    config: Config = ctx.obj["config"]
    keys = list_protected(config, profile)
    if not keys:
        click.echo(f"No protected keys in profile '{profile}'.")
        return
    for key in sorted(keys):
        click.echo(f"  {key}")
