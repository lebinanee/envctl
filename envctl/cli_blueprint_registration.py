"""Registration helper so the main CLI can attach the blueprint group."""

from envctl.cli_blueprint import blueprint_group


def register(cli):
    """Attach the blueprint command group to *cli*."""
    cli.add_command(blueprint_group)
