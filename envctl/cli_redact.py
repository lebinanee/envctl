"""CLI commands for the redact feature."""

from __future__ import annotations

import click

from envctl.config import Config
from envctl.redact import RedactError, redact_profile


@click.group("redact")
def redact_group() -> None:
    """Redact sensitive values in a profile."""


@redact_group.command("show")
@click.argument("profile")
@click.option("--key", "-k", multiple=True, help="Explicitly redact these keys.")
@click.option(
    "--no-auto",
    is_flag=True,
    default=False,
    help="Disable automatic sensitive-key detection.",
)
@click.option("--config", "config_path", default=None, hidden=True)
def show_cmd(profile: str, key: tuple, no_auto: bool, config_path: str | None) -> None:
    """Print profile vars with sensitive values redacted."""
    cfg = Config(config_path)
    try:
        result = redact_profile(
            cfg,
            profile,
            keys=list(key) if key else None,
            auto=not no_auto,
        )
    except RedactError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.redacted:
        click.echo(f"Profile '{profile}' is empty.")
        return

    click.echo(f"Profile: {profile}")
    for k, v in sorted(result.redacted.items()):
        click.echo(f"  {k}={v}")

    click.echo()
    click.echo(
        f"{result.total_redacted} key(s) redacted: "
        + (", ".join(result.redacted_keys) if result.redacted_keys else "none")
    )
