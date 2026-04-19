"""CLI commands for promoting env vars between profiles."""

import click
from envctl.config import Config
from envctl.promote import promote_keys, PromoteError


@click.group("promote")
def promote_group():
    """Promote variables between environment profiles."""


@promote_group.command("run")
@click.argument("src")
@click.argument("dst")
@click.option("--key", "-k", multiple=True, help="Specific key(s) to promote.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in dst.")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def promote_cmd(src, dst, key, overwrite, config_path):
    """Promote variables from SRC profile to DST profile."""
    try:
        config = Config(config_path)
        keys = list(key) if key else None
        results = promote_keys(config, src, dst, keys=keys, overwrite=overwrite)
    except PromoteError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    if not results:
        click.echo("Nothing to promote.")
        return

    for k, status in results.items():
        icon = {"promoted": "✔", "overwritten": "↺", "skipped": "–"}.get(status, "?")
        click.echo(f"  {icon} {k}: {status}")

    promoted = sum(1 for s in results.values() if s in ("promoted", "overwritten"))
    click.echo(f"\nDone. {promoted}/{len(results)} key(s) promoted from '{src}' → '{dst}'.")
