"""CLI commands for reordering keys within a profile."""
from __future__ import annotations

import click

from envctl.config import Config
from envctl.reorder import ReorderError, reorder_profile


@click.group("reorder")
def reorder_group() -> None:
    """Reorder keys within a profile."""


@reorder_group.command("apply")
@click.argument("profile")
@click.option("--alpha", is_flag=True, default=False, help="Sort keys alphabetically.")
@click.option("--reverse", is_flag=True, default=False, help="Reverse the resulting order.")
@click.option(
    "--keys",
    default=None,
    help="Comma-separated list of keys specifying desired order.",
)
@click.option("--config", "config_path", default=None, hidden=True)
def apply_cmd(
    profile: str,
    alpha: bool,
    reverse: bool,
    keys: str | None,
    config_path: str | None,
) -> None:
    """Reorder keys in PROFILE."""
    cfg = Config(config_path) if config_path else Config()
    key_list = [k.strip() for k in keys.split(",") if k.strip()] if keys else None

    try:
        result = reorder_profile(
            cfg,
            profile,
            keys=key_list,
            alphabetical=alpha,
            reverse=reverse,
        )
    except ReorderError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.changed:
        click.echo(f"Profile '{profile}' order unchanged.")
        return

    click.echo(f"Profile '{profile}' reordered ({len(result.new_order)} keys):")
    for key in result.new_order:
        click.echo(f"  {key}")
