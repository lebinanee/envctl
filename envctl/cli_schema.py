"""CLI commands for schema management."""
import click

from envctl.config import Config
from envctl.schema import (
    SchemaError,
    SchemaField,
    add_field,
    get_schema,
    remove_field,
    validate_against_schema,
)


@click.group("schema")
def schema_group() -> None:
    """Manage the environment variable schema."""


@schema_group.command("add")
@click.argument("key")
@click.option("--optional", is_flag=True, default=False, help="Mark field as optional.")
@click.option("--default", "default_val", default=None, help="Default value for optional fields.")
@click.option("--description", default="", help="Human-readable description.")
@click.pass_context
def add_cmd(ctx: click.Context, key: str, optional: bool, default_val: str | None, description: str) -> None:
    """Add or update a schema field."""
    cfg: Config = ctx.obj["config"]
    f = SchemaField(key=key, required=not optional, default=default_val, description=description)
    add_field(cfg, f)
    click.echo(f"Schema field '{key}' added.")


@schema_group.command("remove")
@click.argument("key")
@click.pass_context
def remove_cmd(ctx: click.Context, key: str) -> None:
    """Remove a schema field."""
    cfg: Config = ctx.obj["config"]
    if remove_field(cfg, key):
        click.echo(f"Schema field '{key}' removed.")
    else:
        click.echo(f"Schema field '{key}' not found.", err=True)
        raise SystemExit(1)


@schema_group.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List all schema fields."""
    cfg: Config = ctx.obj["config"]
    fields = get_schema(cfg)
    if not fields:
        click.echo("No schema fields defined.")
        return
    for f in fields:
        req_label = "required" if f.required else "optional"
        default_label = f" (default: {f.default})" if f.default is not None else ""
        desc_label = f" — {f.description}" if f.description else ""
        click.echo(f"  {f.key}  [{req_label}]{default_label}{desc_label}")


@schema_group.command("validate")
@click.argument("profile")
@click.pass_context
def validate_cmd(ctx: click.Context, profile: str) -> None:
    """Validate a profile against the schema."""
    cfg: Config = ctx.obj["config"]
    violations = validate_against_schema(cfg, profile)
    if not violations:
        click.echo(f"Profile '{profile}' is valid.")
    else:
        for v in violations:
            click.echo(f"  FAIL  {v}", err=True)
        raise SystemExit(1)
