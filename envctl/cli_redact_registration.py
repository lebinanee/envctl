"""Register the redact command group with the root CLI."""

from __future__ import annotations

from envctl.cli_redact import redact_group


def register(cli) -> None:  # pragma: no cover
    """Attach the redact command group to *cli*."""
    cli.add_command(redact_group)
