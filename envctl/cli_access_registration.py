"""Registration helper for the access CLI group."""
from envctl.cli_access import access_group


def register(cli):
    cli.add_command(access_group)
