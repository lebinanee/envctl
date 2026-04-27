"""CLI commands for key annotations."""
from __future__ import annotations

import click

from envctl.annotate import AnnotateError, get_annotation, list_annotations, remove_annotation, set_annotation
from envctl.config import Config


@click.group("annotate")
def annotate_group():
    """Attach notes to environment variable keys."""


@annotate_group.command("set")
@click.argument("profile")
@click.argument("key")
@click.argument("note")
def set_cmd(profile: str, key: str, note: str):
    """Attach NOTE to KEY in PROFILE."""
    config = Config()
    try:
        set_annotation(config, profile, key, note)
        click.echo(f"Annotated '{key}' in '{profile}'.")
    except AnnotateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@annotate_group.command("get")
@click.argument("profile")
@click.argument("key")
def get_cmd(profile: str, key: str):
    """Show the note for KEY in PROFILE."""
    config = Config()
    try:
        note = get_annotation(config, profile, key)
    except AnnotateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if note is None:
        click.echo(f"No annotation for '{key}' in '{profile}'.")
    else:
        click.echo(note)


@annotate_group.command("remove")
@click.argument("profile")
@click.argument("key")
def remove_cmd(profile: str, key: str):
    """Remove the annotation for KEY in PROFILE."""
    config = Config()
    try:
        removed = remove_annotation(config, profile, key)
    except AnnotateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if removed:
        click.echo(f"Removed annotation for '{key}' in '{profile}'.")
    else:
        click.echo(f"No annotation found for '{key}' in '{profile}'.")


@annotate_group.command("list")
@click.argument("profile")
def list_cmd(profile: str):
    """List all annotations for PROFILE."""
    config = Config()
    try:
        annotations = list_annotations(config, profile)
    except AnnotateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not annotations:
        click.echo(f"No annotations for profile '{profile}'.")
        return
    for key, note in sorted(annotations.items()):
        click.echo(f"  {key}: {note}")
