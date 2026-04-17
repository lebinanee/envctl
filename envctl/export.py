"""Export environment variables to shell-compatible or .env file formats."""

import os
from typing import Optional


SUPPORTED_FORMATS = ("dotenv", "shell")


class ExportError(Exception):
    pass


def _escape(value: str) -> str:
    """Wrap value in double quotes, escaping inner double quotes."""
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def render(variables: dict, fmt: str = "dotenv") -> str:
    """Render a variables dict to a string in the requested format."""
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")

    lines = []
    for key, value in sorted(variables.items()):
        if fmt == "dotenv":
            lines.append(f"{key}={_escape(str(value))}")
        elif fmt == "shell":
            lines.append(f"export {key}={_escape(str(value))}")
    return "\n".join(lines) + ("\n" if lines else "")


def export_to_file(
    config,
    env: str,
    output_path: str,
    fmt: str = "dotenv",
    overwrite: bool = False,
) -> str:
    """Write environment variables for *env* to *output_path*."""
    if not overwrite and os.path.exists(output_path):
        raise ExportError(
            f"File '{output_path}' already exists. Use overwrite=True to replace it."
        )

    variables = config.get_profile(env)
    if variables is None:
        raise ExportError(f"No profile found for environment '{env}'.")

    content = render(variables, fmt=fmt)
    with open(output_path, "w") as fh:
        fh.write(content)
    return output_path
