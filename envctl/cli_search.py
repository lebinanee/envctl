"""CLI commands for searching environment variables."""
import click
from envctl.config import Config
from envctl.search import search_profiles, format_search_results, SearchError


@click.group("search")
def search_group():
    """Search keys/values across profiles."""


@search_group.command("find")
@click.argument("query")
@click.option("--profile", "-p", multiple=True, help="Limit to specific profiles.")
@click.option("--keys-only", is_flag=True, default=False, help="Search keys only.")
@click.option("--values-only", is_flag=True, default=False, help="Search values only.")
@click.option("--case-sensitive", is_flag=True, default=False)
@click.pass_context
def find_cmd(ctx, query, profile, keys_only, values_only, case_sensitive):
    """Find QUERY in environment variable keys and/or values."""
    config: Config = ctx.obj["config"]

    match_keys = not values_only
    match_values = not keys_only

    try:
        results = search_profiles(
            config,
            query,
            profiles=list(profile) if profile else None,
            match_keys=match_keys,
            match_values=match_values,
            case_sensitive=case_sensitive,
        )
    except SearchError as e:
        raise click.ClickException(str(e))

    click.echo(format_search_results(results))
