"""CLI commands for namespace management."""
from __future__ import annotations

import click

from envctl.config import Config
from envctl.namespace import (
    NamespaceError,
    delete_namespace,
    get_namespace,
    list_namespaces,
    rename_namespace,
    set_namespace,
)


@click.group("namespace", help="Manage key namespaces within a profile.")
def namespace_group() -> None:
    pass


@namespace_group.command("list")
@click.option("--env", default=None, help="Target environment (default: active).")
def list_cmd(env: str | None) -> None:
    """List all namespaces in a profile."""
    cfg = Config()
    profile_name = env or cfg.get_active_env()
    profile = cfg.get_profile(profile_name)
    ns_list = list_namespaces(profile)
    if not ns_list:
        click.echo(f"No namespaces found in '{profile_name}'.")
        return
    for ns in ns_list:
        click.echo(ns)


@namespace_group.command("show")
@click.argument("namespace")
@click.option("--env", default=None, help="Target environment.")
def show_cmd(namespace: str, env: str | None) -> None:
    """Show all keys belonging to NAMESPACE."""
    cfg = Config()
    profile_name = env or cfg.get_active_env()
    profile = cfg.get_profile(profile_name)
    pairs = get_namespace(profile, namespace)
    if not pairs:
        click.echo(f"No keys found under namespace '{namespace}'.")
        return
    for k, v in sorted(pairs.items()):
        click.echo(f"{k}={v}")


@namespace_group.command("delete")
@click.argument("namespace")
@click.option("--env", default=None, help="Target environment.")
def delete_cmd(namespace: str, env: str | None) -> None:
    """Delete all keys under NAMESPACE."""
    cfg = Config()
    profile_name = env or cfg.get_active_env()
    profile = cfg.get_profile(profile_name)
    count = delete_namespace(profile, namespace)
    cfg.set_profile(profile_name, profile)
    cfg.save()
    click.echo(f"Removed {count} key(s) from namespace '{namespace}'.")


@namespace_group.command("rename")
@click.argument("old_namespace")
@click.argument("new_namespace")
@click.option("--env", default=None, help="Target environment.")
def rename_cmd(old_namespace: str, new_namespace: str, env: str | None) -> None:
    """Rename OLD_NAMESPACE to NEW_NAMESPACE."""
    cfg = Config()
    profile_name = env or cfg.get_active_env()
    profile = cfg.get_profile(profile_name)
    try:
        count = rename_namespace(profile, old_namespace, new_namespace)
    except NamespaceError as exc:
        raise click.ClickException(str(exc)) from exc
    cfg.set_profile(profile_name, profile)
    cfg.save()
    click.echo(f"Renamed {count} key(s) from '{old_namespace}' → '{new_namespace}'.")
