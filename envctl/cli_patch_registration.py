"""Register the patch command group with the root CLI."""

from envctl.cli_patch import patch_group


def register(cli) -> None:  # type: ignore[type-arg]
    """Attach patch_group to *cli*."""
    cli.add_command(patch_group)
