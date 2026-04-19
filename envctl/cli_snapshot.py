"""CLI commands for snapshot management."""

import click
from envctl.config import Config
from envctl.snapshot import take_snapshot, list_snapshots, restore_snapshot, delete_snapshot, SnapshotError


@click.group("snapshot")
def snapshot_group():
    """Manage environment snapshots."""


@snapshot_group.command("take")
@click.argument("env")
@click.option("--label", "-l", default="", help="Optional label for the snapshot.")
def take_cmd(env: str, label: str):
    """Take a snapshot of ENV profile."""
    config = Config()
    try:
        entry = take_snapshot(config, env, label or None)
        click.echo(f"Snapshot taken for '{env}' at {entry['timestamp']}.")
        if entry["label"]:
            click.echo(f"  Label: {entry['label']}")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@snapshot_group.command("list")
@click.option("--env", "-e", default=None, help="Filter by environment name.")
def list_cmd(env):
    """List all snapshots."""
    snapshots = list_snapshots(env=env)
    if not snapshots:
        click.echo("No snapshots found.")
        return
    for i, s in enumerate(snapshots):
        label = f" [{s['label']}]" if s["label"] else ""
        click.echo(f"{i:>3}  {s['env']:<12} {s['timestamp']}{label}  ({len(s['vars'])} vars)")


@snapshot_group.command("restore")
@click.argument("index", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def restore_cmd(index: int, yes: bool):
    """Restore snapshot by INDEX."""
    config = Config()
    try:
        snapshots = list_snapshots()
        if index < 0 or index >= len(snapshots):
            click.echo(f"Error: No snapshot at index {index}.", err=True)
            raise SystemExit(1)
        entry = snapshots[index]
        if not yes:
            click.confirm(
                f"Restore snapshot {index} for '{entry['env']}' taken {entry['timestamp']}?",
                abort=True,
            )
        entry = restore_snapshot(config, index)
        click.echo(f"Restored snapshot {index} for '{entry['env']}' (taken {entry['timestamp']}).")
    except click.Abort:
        click.echo("Aborted.")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@snapshot_group.command("delete")
@click.argument("index", type=int)
def delete_cmd(index: int):
    """Delete snapshot by INDEX."""
    try:
        delete_snapshot(index)
        click.echo(f"Snapshot {index} deleted.")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
