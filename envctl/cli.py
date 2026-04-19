"""Main CLI entry-point for envctl."""
import click
from envctl.config import Config
from envctl.cli_sync import sync_group
from envctl.cli_audit import audit_group
from envctl.cli_snapshot import snapshot_group
from envctl.cli_import import import_group
from envctl.cli_compare import compare_group
from envctl.cli_rename import rename_group
from envctl.cli_copy import copy_group
from envctl.cli_search import search_group
from envctl.cli_tag import tag_group
from envctl.cli_pin import pin_group
from envctl.cli_promote import promote_group
from envctl.cli_template import template_group
from envctl.cli_mask import mask_group
from envctl.cli_history import history_group
from envctl.cli_watch import watch_group
from envctl.cli_rollback import rollback_group


@click.group()
def cli():
    """envctl — manage and sync environment variables."""


@cli.command()
@click.argument("env")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def use(env: str, config_path: str):
    """Switch the active environment."""
    cfg = Config(config_path)
    try:
        cfg.set_active_env(env)
        cfg.save()
        click.echo(f"Switched to environment: {env}")
    except ValueError as exc:
        raise click.ClickException(str(exc))


@cli.command()
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def status(config_path: str):
    """Show active environment."""
    cfg = Config(config_path)
    click.echo(f"Active environment: {cfg.get_active_env()}")


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--profile", default=None)
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def set_var(key: str, value: str, profile: str, config_path: str):
    """Set a variable in a profile."""
    cfg = Config(config_path)
    env = profile or cfg.get_active_env()
    data = cfg.get_profile(env) or {}
    data[key] = value
    cfg.set_profile(env, data)
    cfg.save()
    click.echo(f"Set {key} in [{env}]")


@cli.command("list")
@click.option("--profile", default=None)
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def list_vars(profile: str, config_path: str):
    """List variables in a profile."""
    cfg = Config(config_path)
    env = profile or cfg.get_active_env()
    data = cfg.get_profile(env) or {}
    if not data:
        click.echo(f"No variables in [{env}].")
        return
    for k, v in data.items():
        click.echo(f"{k}={v}")


for grp in [
    sync_group, audit_group, snapshot_group, import_group, compare_group,
    rename_group, copy_group, search_group, tag_group, pin_group,
    promote_group, template_group, mask_group, history_group, watch_group,
    rollback_group,
]:
    cli.add_command(grp)
