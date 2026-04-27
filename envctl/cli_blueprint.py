"""CLI commands for the blueprint feature."""

from __future__ import annotations

import click

from envctl.blueprint import (
    BlueprintError,
    apply_blueprint,
    delete_blueprint,
    get_blueprint,
    list_blueprints,
    save_blueprint,
)
from envctl.config import Config


@click.group("blueprint")
def blueprint_group():
    """Manage reusable key blueprints."""


@blueprint_group.command("save")
@click.argument("name")
@click.argument("keys", nargs=-1, required=True)  # KEY=VALUE pairs
@click.option("--desc", default="", help="Short description.")
def save_cmd(name, keys, desc):
    """Save a blueprint from KEY=VALUE pairs."""
    parsed: dict = {}
    for pair in keys:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=VALUE, got {pair!r}")
        k, v = pair.split("=", 1)
        parsed[k] = v
    cfg = Config()
    try:
        bp = save_blueprint(cfg, name, parsed, description=desc)
        click.echo(f"Blueprint '{bp.name}' saved with {len(bp.keys)} key(s).")
    except BlueprintError as exc:
        raise click.ClickException(str(exc))


@blueprint_group.command("list")
def list_cmd():
    """List all saved blueprints."""
    cfg = Config()
    blueprints = list_blueprints(cfg)
    if not blueprints:
        click.echo("No blueprints saved.")
        return
    for bp in blueprints:
        desc = f"  # {bp.description}" if bp.description else ""
        click.echo(f"{bp.name} ({len(bp.keys)} keys){desc}")


@blueprint_group.command("show")
@click.argument("name")
def show_cmd(name):
    """Show keys defined in a blueprint."""
    cfg = Config()
    try:
        bp = get_blueprint(cfg, name)
    except BlueprintError as exc:
        raise click.ClickException(str(exc))
    if bp.description:
        click.echo(f"Description: {bp.description}")
    for k, v in bp.keys.items():
        click.echo(f"  {k}={v}")


@blueprint_group.command("apply")
@click.argument("name")
@click.argument("profile")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys.")
def apply_cmd(name, profile, overwrite):
    """Apply a blueprint to a profile."""
    cfg = Config()
    try:
        applied = apply_blueprint(cfg, name, profile, overwrite=overwrite)
    except BlueprintError as exc:
        raise click.ClickException(str(exc))
    if not applied:
        click.echo("Nothing to apply (all keys already present).")
    else:
        click.echo(f"Applied {len(applied)} key(s) to '{profile}'.")


@blueprint_group.command("delete")
@click.argument("name")
def delete_cmd(name):
    """Delete a blueprint."""
    cfg = Config()
    removed = delete_blueprint(cfg, name)
    if removed:
        click.echo(f"Blueprint '{name}' deleted.")
    else:
        raise click.ClickException(f"Blueprint '{name}' not found.")
