"""CLI commands for change history."""
import click
from datetime import datetime
from envctl.history import get_history, clear_history, HISTORY_FILE


@click.group("history")
def history_group():
    """View and manage key change history."""


@history_group.command("log")
@click.option("--profile", "-p", default=None, help="Filter by profile")
@click.option("--key", "-k", default=None, help="Filter by key")
@click.option("--limit", "-n", default=20, show_default=True, help="Max entries to show")
def log_cmd(profile, key, limit):
    """Show change history."""
    entries = get_history(profile=profile, key=key)
    if not entries:
        click.echo("No history found.")
        return
    for e in entries[-limit:]:
        ts = datetime.fromtimestamp(e.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        old = e.old_value if e.old_value is not None else "(none)"
        new = e.new_value if e.new_value is not None else "(none)"
        click.echo(f"[{ts}] {e.action.upper():8s} {e.profile}/{e.key}  {old} -> {new}")


@history_group.command("clear")
@click.confirmation_option(prompt="Clear all history?")
def clear_cmd():
    """Clear all history entries."""
    clear_history()
    click.echo("History cleared.")
