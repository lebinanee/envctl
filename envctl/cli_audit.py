"""CLI commands for audit log inspection."""

import click
from envctl.audit import get_log, clear_log


@click.group("audit")
def audit_group():
    """View and manage the audit log."""
    pass


@audit_group.command("log")
@click.option("--env", default=None, help="Filter by environment name.")
@click.option("--key", default=None, help="Filter by variable key.")
@click.option("--limit", default=20, show_default=True, help="Max entries to show.")
def log_cmd(env, key, limit):
    """Display recent audit log entries."""
    entries = get_log()

    if env:
        entries = [e for e in entries if e.get("env") == env]
    if key:
        entries = [e for e in entries if e.get("key") == key]

    entries = entries[-limit:]

    if not entries:
        click.echo("No audit log entries found.")
        return

    for e in entries:
        old = e.get("old_value")
        new = e.get("new_value")
        change = ""
        if e["action"] == "set":
            change = f"{old!r} -> {new!r}" if old is not None else f"(new) {new!r}"
        elif e["action"] == "delete":
            change = f"(deleted) {old!r}"
        elif e["action"] == "sync":
            change = f"{old!r} -> {new!r}"
        click.echo(
            f"[{e['timestamp']}] {e['action'].upper():6s} "
            f"{e['env']}.{e['key']}  {change}"
        )


@audit_group.command("clear")
@click.confirmation_option(prompt="Clear the entire audit log?")
def clear_cmd():
    """Clear all audit log entries."""
    clear_log()
    click.echo("Audit log cleared.")
