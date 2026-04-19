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


@click.group()
def cli():
    """envctl — manage and sync environment variables."""


@cli.command()
@click.argument("env")
def use(env):
    """Switch active environment."""
    cfg = Config()
    try:
        cfg.set_active_env(env)
        cfg.save()
        click.echo(f"Switched to {env}")
    except ValueError as e:
        click.echo(str(e), err=True)
        raise SystemExit(1)


@cli.command()
def status():
    """Show active environment."""
    cfg = Config()
    click.echo(f"Active env: {cfg.get_active_env()}")


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--env", default=None)
def set_var(key, value, env):
    """Set a variable in a profile."""
    cfg = Config()
    profile = env or cfg.get_active_env()
    cfg.set_profile_var(profile, key, value)
    cfg.save()
    click.echo(f"Set {key} in {profile}")


@cli.command("list")
@click.option("--env", default=None)
def list_vars(env):
    """List variables in a profile."""
    cfg = Config()
    profile = env or cfg.get_active_env()
    data = cfg.get_profile(profile)
    if not data:
        click.echo("(empty)")
        return
    for k, v in data.items():
        click.echo(f"{k}={v}")


for grp in [sync_group, audit_group, snapshot_group, import_group, compare_group,
            rename_group, copy_group, search_group, tag_group, pin_group,
            promote_group, template_group, mask_group, history_group]:
    cli.add_command(grp)


if __name__ == "__main__":
    cli()
