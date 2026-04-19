"""CLI commands for watch feature."""
import click

from envctl.config import Config
from envctl.watch import WatchError, WatchEvent, watch_profile


@click.group("watch")
def watch_group() -> None:
    """Watch a profile for live changes."""


@watch_group.command("start")
@click.argument("profile")
@click.option("--interval", default=2.0, show_default=True, help="Poll interval in seconds.")
@click.option("--cycles", default=None, type=int, help="Stop after N cycles (default: run forever).")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def start_cmd(profile: str, interval: float, cycles: int, config_path: str) -> None:
    """Watch PROFILE and print diffs as they occur."""
    config = Config(config_path)

    def _on_change(event: WatchEvent) -> None:
        click.echo(f"[{event.profile}] {event.summary()}")
        for key, val in event.added.items():
            click.echo(f"  + {key}={val}")
        for key, val in event.removed.items():
            click.echo(f"  - {key}={val}")
        for key, (old, new) in event.changed.items():
            click.echo(f"  ~ {key}: {old!r} -> {new!r}")

    click.echo(f"Watching profile '{profile}' every {interval}s … (Ctrl+C to stop)")
    try:
        watch_profile(config, profile, _on_change, interval=interval, max_cycles=cycles)
    except WatchError as exc:
        raise click.ClickException(str(exc))
    except KeyboardInterrupt:
        click.echo("\nStopped watching.")
