"""CLI commands for tag management."""
import click
from envctl.config import Config
from envctl.tag import add_tag, remove_tag, list_tags, find_by_tag, TagError


@click.group("tag")
def tag_group():
    """Manage tags on environment variable keys."""


@tag_group.command("add")
@click.argument("profile")
@click.argument("key")
@click.argument("tag")
def add_cmd(profile: str, key: str, tag: str):
    """Add a tag to a key in a profile."""
    config = Config()
    try:
        add_tag(config, profile, key, tag)
        click.echo(f"Tagged '{key}' with '{tag}' in [{profile}].")
    except TagError as e:
        raise click.ClickException(str(e))


@tag_group.command("remove")
@click.argument("profile")
@click.argument("key")
@click.argument("tag")
def remove_cmd(profile: str, key: str, tag: str):
    """Remove a tag from a key."""
    config = Config()
    removed = remove_tag(config, profile, key, tag)
    if removed:
        click.echo(f"Removed tag '{tag}' from '{key}' in [{profile}].")
    else:
        click.echo(f"Tag '{tag}' not found on '{key}'.")


@tag_group.command("list")
@click.argument("profile")
@click.argument("key")
def list_cmd(profile: str, key: str):
    """List tags on a key."""
    config = Config()
    tags = list_tags(config, profile, key)
    if tags:
        click.echo(", ".join(tags))
    else:
        click.echo(f"No tags on '{key}'.")


@tag_group.command("find")
@click.argument("profile")
@click.argument("tag")
def find_cmd(profile: str, tag: str):
    """Find all keys with a given tag."""
    config = Config()
    keys = find_by_tag(config, profile, tag)
    if keys:
        for k in keys:
            click.echo(k)
    else:
        click.echo(f"No keys tagged '{tag}' in [{profile}].")
