"""Helper to register the merge group with the root CLI.

Import and call ``register(cli)`` from ``envctl/cli.py`` to attach the
``merge`` subcommand group without circular imports.
"""

from __future__ import annotations

import click

from envctl.cli_merge import merge_group


def register(cli: click.Group) -> None:
    """Attach the merge command group to *cli*."""
    cli.add_command(merge_group)
