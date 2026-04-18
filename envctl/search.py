"""Search for keys or values across profiles."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from envctl.config import Config


class SearchError(Exception):
    pass


@dataclass
class SearchResult:
    profile: str
    key: str
    value: str
    match_field: str  # 'key' or 'value'


def search_profiles(
    config: Config,
    query: str,
    profiles: Optional[List[str]] = None,
    match_keys: bool = True,
    match_values: bool = True,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Search for query string across keys and/or values in profiles."""
    if not query:
        raise SearchError("Search query must not be empty.")
    if not match_keys and not match_values:
        raise SearchError("At least one of match_keys or match_values must be True.")

    target_profiles = profiles or list(config.data.get("profiles", {}).keys())
    cmp_query = query if case_sensitive else query.lower()
    results: List[SearchResult] = []

    for profile in target_profiles:
        vars_ = config.get_profile(profile)
        if vars_ is None:
            continue
        for key, value in vars_.items():
            cmp_key = key if case_sensitive else key.lower()
            cmp_val = value if case_sensitive else value.lower()
            if match_keys and cmp_query in cmp_key:
                results.append(SearchResult(profile, key, value, "key"))
            elif match_values and cmp_query in cmp_val:
                results.append(SearchResult(profile, key, value, "value"))

    return results


def format_search_results(results: List[SearchResult]) -> str:
    if not results:
        return "No matches found."
    lines = []
    for r in results:
        lines.append(f"[{r.profile}] {r.key}={r.value}  (matched {r.match_field})")
    return "\n".join(lines)
