"""CLI commands for template rendering."""

from __future__ import annotations

import sys

import click

from envctl.config import Config
from envctl.template import TemplateError, render_template


@click.group("template")
def template_group() -> None:
    """Render templates using environment variable values."""


@template_group.command("render")
@click.argument("template_file", type=click.Path(exists=True))
@click.option("--env", default=None, help="Profile to use (default: active env).")
@click.option("--output", "-o", default=None, type=click.Path(), help="Output file.")
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Fail if any placeholder is unresolved.",
)
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def render_cmd(
    template_file: str,
    env: str | None,
    output: str | None,
    strict: bool,
    config_path: str,
) -> None:
    """Render TEMPLATE_FILE substituting {{KEY}} placeholders."""
    cfg = Config(config_path)
    with open(template_file, "r") as fh:
        raw = fh.read()

    try:
        result = render_template(raw, cfg, profile=env, strict=strict)
    except TemplateError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output:
        with open(output, "w") as fh:
            fh.write(result.output)
        click.echo(f"Rendered to {output}")
    else:
        click.echo(result.output, nl=False)

    if result.missing:
        click.echo(
            f"Warning: {len(result.missing)} unresolved placeholder(s): "
            + ", ".join(result.missing),
            err=True,
        )
