"""Tests for envctl.search module."""
import pytest
from unittest.mock import MagicMock
from envctl.search import search_profiles, format_search_results, SearchError


def make_config(profiles: dict):
    config = MagicMock()
    config.data = {"profiles": profiles}
    config.get_profile = lambda name: profiles.get(name)
    return config


def test_search_by_key():
    cfg = make_config({"local": {"DATABASE_URL": "postgres://", "API_KEY": "abc"}})
    results = search_profiles(cfg, "DATABASE", match_keys=True, match_values=False)
    assert len(results) == 1
    assert results[0].key == "DATABASE_URL"
    assert results[0].match_field == "key"


def test_search_by_value():
    cfg = make_config({"local": {"SECRET": "mysecretvalue", "PORT": "8080"}})
    results = search_profiles(cfg, "secret", match_keys=False, match_values=True)
    assert len(results) == 1
    assert results[0].key == "SECRET"
    assert results[0].match_field == "value"


def test_search_case_sensitive_no_match():
    cfg = make_config({"local": {"API_KEY": "AbcDef"}})
    results = search_profiles(cfg, "abcdef", case_sensitive=True)
    assert results == []


def test_search_case_sensitive_match():
    cfg = make_config({"local": {"API_KEY": "AbcDef"}})
    results = search_profiles(cfg, "AbcDef", case_sensitive=True, match_keys=False, match_values=True)
    assert len(results) == 1


def test_search_multiple_profiles():
    cfg = make_config({
        "local": {"TOKEN": "abc"},
        "prod": {"TOKEN": "xyz", "DB": "postgres"},
    })
    results = search_profiles(cfg, "TOKEN")
    profiles_hit = {r.profile for r in results}
    assert profiles_hit == {"local", "prod"}


def test_search_limit_to_profile():
    cfg = make_config({
        "local": {"TOKEN": "abc"},
        "prod": {"TOKEN": "xyz"},
    })
    results = search_profiles(cfg, "TOKEN", profiles=["local"])
    assert all(r.profile == "local" for r in results)


def test_search_empty_query_raises():
    cfg = make_config({"local": {}})
    with pytest.raises(SearchError, match="empty"):
        search_profiles(cfg, "")


def test_search_no_fields_raises():
    cfg = make_config({"local": {"KEY": "val"}})
    with pytest.raises(SearchError):
        search_profiles(cfg, "KEY", match_keys=False, match_values=False)


def test_format_no_results():
    assert format_search_results([]) == "No matches found."


def test_format_results():
    cfg = make_config({"local": {"API_KEY": "secret"}})
    results = search_profiles(cfg, "API_KEY")
    output = format_search_results(results)
    assert "API_KEY" in output
    assert "local" in output
