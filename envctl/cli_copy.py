"""CLI commands for copying keys between profiles."""
import click
from envctl.config import Config
from envctl.copy import copy_keys, CopyError


@click.group("copy")
def copy_group():
    """Copy keys between profiles."""


@copy_group.command("run")
@click.argument("src")
@click.argument("dst")
@click.option("--key", "-k", multiple=True, help="Specific key(s) to copy.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys.")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def copy_cmd(src, dst, key, overwrite, config_path):
    """Copy keys from SRC profile to DST profile."""
    try:
        cfg = Config(config_path)
        keys = list(key) if key else None
        result = copy_keys(cfg, src, dst, keys=keys, overwrite=overwrite)
        _print_copy_result(result)
    except CopyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


def _print_copy_result(result):
    """Print a human-readable summary of a copy operation result.

    Args:
        result: A dict with 'copied' and 'skipped' lists returned by copy_keys.
    """
    if result["copied"]:
        click.echo(f"Copied: {', '.join(result['copied'])}")
    if result["skipped"]:
        click.echo(f"Skipped (already exist): {', '.join(result['skipped'])}")
    if not result["copied"] and not result["skipped"]:
        click.echo("Nothing to copy.")
