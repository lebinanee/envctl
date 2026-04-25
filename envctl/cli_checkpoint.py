"""CLI commands for checkpoint management."""
from __future__ import annotations

import click

from envctl.checkpoint import (
    CheckpointError,
    create_checkpoint,
    delete_checkpoint,
    list_checkpoints,
    restore_checkpoint,
)
from envctl.config import Config


@click.group("checkpoint")
def checkpoint_group():
    """Manage named environment checkpoints."""


@checkpoint_group.command("create")
@click.argument("profile")
@click.argument("name")
@click.option("--note", default="", help="Optional note for this checkpoint")
def create_cmd(profile: str, name: str, note: str):
    """Create a named checkpoint for PROFILE."""
    cfg = Config()
    try:
        entry = create_checkpoint(cfg, profile, name, note)
        click.echo(f"Checkpoint '{entry['name']}' created for profile '{profile}'.")
        if note:
            click.echo(f"Note: {note}")
    except CheckpointError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@checkpoint_group.command("list")
@click.option("--profile", default=None, help="Filter by profile")
def list_cmd(profile: str | None):
    """List all checkpoints."""
    cfg = Config()
    entries = list_checkpoints(cfg, profile)
    if not entries:
        click.echo("No checkpoints found.")
        return
    for e in entries:
        ts = e["timestamp"]
        note = f"  # {e['note']}" if e["note"] else ""
        click.echo(f"[{e['profile']}] {e['name']}  (ts={ts:.0f}){note}")


@checkpoint_group.command("restore")
@click.argument("profile")
@click.argument("name")
def restore_cmd(profile: str, name: str):
    """Restore PROFILE to checkpoint NAME."""
    cfg = Config()
    try:
        vars_ = restore_checkpoint(cfg, profile, name)
        click.echo(f"Restored '{profile}' to checkpoint '{name}' ({len(vars_)} keys).")
    except CheckpointError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@checkpoint_group.command("delete")
@click.argument("profile")
@click.argument("name")
def delete_cmd(profile: str, name: str):
    """Delete checkpoint NAME for PROFILE."""
    cfg = Config()
    deleted = delete_checkpoint(cfg, profile, name)
    if deleted:
        click.echo(f"Checkpoint '{name}' deleted.")
    else:
        click.echo(f"Checkpoint '{name}' not found for profile '{profile}'.")
