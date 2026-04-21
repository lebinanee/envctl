"""Registration helper for the TTL CLI group."""
from envctl.cli_ttl import ttl_group


def register(cli):
    """Attach the ttl command group to the root CLI."""
    cli.add_command(ttl_group)
