"""CLI commands for the patch feature."""

from __future__ import annotations

import click

from envctl.config import Config
from envctl.patch import patch_profile, PatchError


@click.group("patch")
def patch_group() -> None:
    """Apply key/value patches to a profile."""


@patch_group.command("apply")
@click.argument("profile")
@click.option("-s", "--set", "pairs", multiple=True, metavar="KEY=VALUE",
              required=True, help="Key=value pair(s) to patch.")
@click.option("--no-overwrite", is_flag=True, default=False,
              help="Skip keys that already exist in the profile.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview changes without saving.")
@click.option("--config", "config_path", default=None, hidden=True)
def apply_cmd(
    profile: str,
    pairs: tuple,
    no_overwrite: bool,
    dry_run: bool,
    config_path: str | None,
) -> None:
    """Patch PROFILE with one or more KEY=VALUE pairs."""
    cfg = Config(config_path) if config_path else Config()

    patch: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {pair!r}")
        k, _, v = pair.partition("=")
        patch[k.strip()] = v.strip()

    try:
        result = patch_profile(
            cfg,
            profile,
            patch,
            overwrite=not no_overwrite,
            dry_run=dry_run,
        )
    except PatchError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    prefix = "[dry-run] " if dry_run else ""

    for key, value in result.applied.items():
        click.echo(f"{prefix}patched  {key}={value}")
    for key, value in result.skipped.items():
        click.echo(f"{prefix}skipped  {key} (already set)")
    for msg in result.errors:
        click.echo(f"invalid  {msg}", err=True)

    click.echo(
        f"\n{prefix}Done: {result.total_applied} applied, "
        f"{result.total_skipped} skipped, {len(result.errors)} error(s)."
    )
