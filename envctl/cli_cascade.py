"""CLI commands for the cascade feature."""

from __future__ import annotations

import click

from envctl.cascade import CascadeError, cascade_profiles, format_cascade_report
from envctl.config import Config


@click.group("cascade")
def cascade_group() -> None:
    """Resolve effective vars by layering profiles."""


@cascade_group.command("resolve")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--keys", "-k", multiple=True, help="Restrict output to these keys.")
@click.option("--config", "config_path", default=None, hidden=True)
@click.option("--sources", is_flag=True, default=False, help="Show which profile each key came from.")
def resolve_cmd(
    profiles: tuple,
    keys: tuple,
    config_path: str | None,
    sources: bool,
) -> None:
    """Resolve effective environment by layering PROFILES (left = lowest priority)."""
    cfg = Config(path=config_path) if config_path else Config()
    try:
        result = cascade_profiles(cfg, list(profiles), keys=list(keys) or None)
    except CascadeError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.effective:
        click.echo("No variables resolved.")
        return

    if sources:
        click.echo(format_cascade_report(result))
    else:
        for key in sorted(result.effective):
            click.echo(f"{key}={result.effective[key]}")

    click.echo(
        f"\n{result.total_keys} key(s) resolved from {len(profiles)} profile(s).",
        err=True,
    )
