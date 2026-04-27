"""CLI commands for variable resolution / interpolation."""
from __future__ import annotations

import click

from envctl.config import Config
from envctl.resolve import ResolveError, resolve_profile


@click.group("resolve", help="Resolve variable references within a profile.")
def resolve_group() -> None:  # pragma: no cover
    pass


@resolve_group.command("show")
@click.argument("profile")
@click.option("--config", "cfg_path", default="envctl.json", show_default=True)
@click.option(
    "--only-issues",
    is_flag=True,
    default=False,
    help="Only show unresolved references or detected cycles.",
)
def show_cmd(profile: str, cfg_path: str, only_issues: bool) -> None:
    """Show resolved values for PROFILE."""
    cfg = Config(cfg_path)
    raw = cfg.get_profile(profile)
    if raw is None:
        raise click.ClickException(f"Profile '{profile}' not found.")

    result = resolve_profile(raw)

    if result.cycles:
        click.echo(click.style("Cycles detected:", fg="red"))
        for c in result.cycles:
            click.echo(f"  {c}")

    if result.unresolved:
        click.echo(click.style("Unresolved references:", fg="yellow"))
        for u in result.unresolved:
            click.echo(f"  ${u}")

    if only_issues:
        if not result.has_issues:
            click.echo("No issues found.")
        return

    if not result.resolved:
        click.echo("(empty profile)")
        return

    click.echo(f"Resolved values for '{profile}':")
    for key, val in sorted(result.resolved.items()):
        original = raw.get(key, "")
        marker = " *" if val != original else ""
        click.echo(f"  {key}={val}{marker}")

    if any(v != raw.get(k, "") for k, v in result.resolved.items()):
        click.echo("\n(* = value was interpolated)")
