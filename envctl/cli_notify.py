"""CLI commands for managing notification hooks."""
from __future__ import annotations

import click

from envctl.config import Config
from envctl.notify import NotifyError, add_rule, remove_rule, list_rules


@click.group("notify", help="Manage webhook notification rules for profile changes.")
def notify_group():
    pass


@notify_group.command("add", help="Register a webhook for a profile (optionally scoped to keys).")
@click.argument("profile")
@click.argument("webhook_url")
@click.option("--key", "keys", multiple=True, help="Restrict to specific keys (repeatable).")
@click.option("--label", default=None, help="Human-readable label for this rule.")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def add_cmd(profile, webhook_url, keys, label, config_path):
    try:
        cfg = Config(config_path)
        rule = add_rule(cfg, profile, webhook_url, keys=list(keys) or None, label=label)
        scope = f" (keys: {', '.join(rule.keys)})" if rule.keys else " (all keys)"
        click.echo(f"Notification rule added for '{profile}'{scope} → {webhook_url}")
    except NotifyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@notify_group.command("remove", help="Remove a webhook rule for a profile.")
@click.argument("profile")
@click.argument("webhook_url")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def remove_cmd(profile, webhook_url, config_path):
    cfg = Config(config_path)
    removed = remove_rule(cfg, profile, webhook_url)
    if removed:
        click.echo(f"Rule removed for '{profile}' → {webhook_url}")
    else:
        click.echo(f"No matching rule found for '{profile}' → {webhook_url}", err=True)
        raise SystemExit(1)


@notify_group.command("list", help="List all notification rules, optionally filtered by profile.")
@click.option("--profile", default=None, help="Filter by profile name.")
@click.option("--config", "config_path", default="envctl.json", show_default=True)
def list_cmd(profile, config_path):
    cfg = Config(config_path)
    rules = list_rules(cfg, profile=profile)
    if not rules:
        click.echo("No notification rules configured.")
        return
    for rule in rules:
        label_str = f" [{rule.label}]" if rule.label else ""
        keys_str = ", ".join(rule.keys) if rule.keys else "*"
        click.echo(f"  {rule.profile}{label_str}  keys={keys_str}  url={rule.webhook_url}")
