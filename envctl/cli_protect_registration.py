"""Registration helper for the protect CLI group."""
from envctl.cli_protect import protect_group


def register(cli):
    cli.add_command(protect_group)
