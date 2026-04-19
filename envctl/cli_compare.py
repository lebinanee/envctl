"""CLI commands for comparing environment profiles."""

import click
from envctl.config import Config
from envctl.compare import compare_profiles, format_report, CompareError


@click.group(name="compare")
def compare_group():
    """Compare variables between two environment profiles."""


@compare_group.command(name="run")
@click.argument("source")
@click.argument("target")
@click.option("--keys", "-k", multiple=True, help="Limit comparison to specific keys.")
@click.option("--diff-only", is_flag=True, default=False, help="Show only differing keys.")
@click.option("--config", "config_path", default=None, help="Path to config file.")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format.")
def compare_cmd(source, target, keys, diff_only, config_path, output):
    """Compare SOURCE profile against TARGET profile."""
    try:
        cfg = Config(path=config_path)
        entries = compare_profiles(
            cfg,
            source,
            target,
            keys=list(keys) if keys else None,
            only_diff=diff_only,
        )
        if output == "json":
            import json
            click.echo(json.dumps([e.__dict__ for e in entries], indent=2))
        else:
            report = format_report(entries, source, target)
            click.echo(report)
    except CompareError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
