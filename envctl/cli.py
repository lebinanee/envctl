"""CLI entry point for envctl."""

import click
from envctl.config import Config, VALID_ENVS


@click.group()
@click.pass_context
def cli(ctx):
    """envctl — manage and sync environment variables across configs."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config()


@cli.command()
@click.argument("env", type=click.Choice(list(VALID_ENVS)))
@click.pass_context
def use(ctx, env):
    """Switch the active environment."""
    config: Config = ctx.obj["config"]
    config.set_active_env(env)
    click.echo(f"Switched active environment to '{env}'.")


@cli.command()
@click.pass_context
def status(ctx):
    """Show the current active environment."""
    config: Config = ctx.obj["config"]
    active = config.get_active_env()
    envs = config.list_envs()
    click.echo(f"Active environment : {active}")
    click.echo(f"Configured profiles: {', '.join(envs) if envs else 'none'}")


@cli.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--env", default=None, help="Target environment (defaults to active).")
@click.pass_context
def set_var(ctx, key, value, env):
    """Set an environment variable in a profile."""
    config: Config = ctx.obj["config"]
    target_env = env or config.get_active_env()
    profile = config.get_profile(target_env)
    profile[key] = value
    config.set_profile(target_env, profile)
    click.echo(f"Set {key}={value} in '{target_env}'.")


@cli.command(name="list")
@click.option("--env", default=None, help="Target environment (defaults to active).")
@click.pass_context
def list_vars(ctx, env):
    """List all variables in a profile."""
    config: Config = ctx.obj["config"]
    target_env = env or config.get_active_env()
    profile = config.get_profile(target_env)
    if not profile:
        click.echo(f"No variables set for '{target_env}'.")
        return
    click.echo(f"Variables for '{target_env}':")
    for k, v in profile.items():
        click.echo(f"  {k}={v}")


if __name__ == "__main__":
    cli()
