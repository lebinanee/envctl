"""Register the normalize command group with the root CLI."""
from envctl.cli_normalize import normalize_group


def register(cli):
    """Attach normalize_group to *cli*."""
    cli.add_command(normalize_group)
