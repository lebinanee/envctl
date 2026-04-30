"""CLI commands for access control."""
import click
from envctl.access import AccessError, set_access, revoke_access, check_access, list_access
from envctl.config import Config


@click.group("access")
def access_group():
    """Manage key-level access control by role."""


@access_group.command("grant")
@click.argument("profile")
@click.argument("role")
@click.argument("keys", nargs=-1, required=True)
@click.option("--mode", default="read", show_default=True, type=click.Choice(["read", "write"]))
@click.pass_context
def grant_cmd(ctx, profile, role, keys, mode):
    """Grant ROLE access to KEYS in PROFILE."""
    cfg: Config = ctx.obj
    try:
        set_access(cfg, profile, role, list(keys), mode)
        click.echo(f"Granted {mode} access to {len(keys)} key(s) for role '{role}' in '{profile}'.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)


@access_group.command("revoke")
@click.argument("profile")
@click.argument("role")
@click.option("--mode", default=None, type=click.Choice(["read", "write"]), help="Mode to revoke; omit for all.")
@click.pass_context
def revoke_cmd(ctx, profile, role, mode):
    """Revoke ROLE's access in PROFILE."""
    cfg: Config = ctx.obj
    removed = revoke_access(cfg, profile, role, mode)
    if removed:
        label = f"'{mode}' mode" if mode else "all modes"
        click.echo(f"Revoked {label} for role '{role}' in '{profile}'.")
    else:
        click.echo(f"No access entry found for role '{role}' in '{profile}'.")


@access_group.command("check")
@click.argument("profile")
@click.argument("role")
@click.argument("key")
@click.option("--mode", default="read", show_default=True, type=click.Choice(["read", "write"]))
@click.pass_context
def check_cmd(ctx, profile, role, key, mode):
    """Check if ROLE can access KEY in PROFILE."""
    cfg: Config = ctx.obj
    allowed = check_access(cfg, profile, role, key, mode)
    status = "ALLOWED" if allowed else "DENIED"
    click.echo(f"{status}: role '{role}' {mode} access to '{key}' in '{profile}'.")


@access_group.command("list")
@click.argument("profile")
@click.pass_context
def list_cmd(ctx, profile):
    """List all access rules for PROFILE."""
    cfg: Config = ctx.obj
    acl = list_access(cfg, profile)
    if not acl:
        click.echo(f"No access rules defined for '{profile}'.")
        return
    for role, modes in sorted(acl.items()):
        for mode, keys in sorted(modes.items()):
            click.echo(f"  {role}  [{mode}]  {', '.join(keys)}")
