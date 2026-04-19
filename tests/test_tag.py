"""Tests for envctl.tag module."""
import pytest
from unittest.mock import MagicMock
from envctl.tag import add_tag, remove_tag, list_tags, find_by_tag, TagError, TAGS_KEY


def make_config(profile_data=None):
    config = MagicMock()
    store = {"local": dict(profile_data or {})}

    def get_profile(p):
        return store.get(p, {})

    def set_profile(p, d):
        store[p] = d

    config.get_profile.side_effect = get_profile
    config.set_profile.side_effect = set_profile
    config.save = MagicMock()
    return config


def test_add_tag_success():
    config = make_config({"API_KEY": "abc"})
    add_tag(config, "local", "API_KEY", "sensitive")
    data = config.get_profile("local")
    assert "sensitive" in data[TAGS_KEY]["API_KEY"]


def test_add_tag_missing_key_raises():
    config = make_config({})
    with pytest.raises(TagError, match="not found"):
        add_tag(config, "local", "MISSING", "tag")


def test_add_tag_no_duplicates():
    config = make_config({"DB_URL": "postgres://"})
    add_tag(config, "local", "DB_URL", "infra")
    add_tag(config, "local", "DB_URL", "infra")
    tags = list_tags(config, "local", "DB_URL")
    assert tags.count("infra") == 1


def test_remove_tag_success():
    config = make_config({"TOKEN": "xyz", TAGS_KEY: {"TOKEN": ["secret"]}})
    result = remove_tag(config, "local", "TOKEN", "secret")
    assert result is True
    assert list_tags(config, "local", "TOKEN") == []


def test_remove_tag_not_present_returns_false():
    config = make_config({"TOKEN": "xyz"})
    result = remove_tag(config, "local", "TOKEN", "ghost")
    assert result is False


def test_list_tags_empty():
    config = make_config({"FOO": "bar"})
    assert list_tags(config, "local", "FOO") == []


def test_find_by_tag():
    tags = {"API_KEY": ["sensitive"], "DB_PASS": ["sensitive", "infra"], "PORT": ["infra"]}
    config = make_config({"API_KEY": "a", "DB_PASS": "b", "PORT": "c", TAGS_KEY: tags})
    result = find_by_tag(config, "local", "sensitive")
    assert set(result) == {"API_KEY", "DB_PASS"}


def test_find_by_tag_no_match():
    config = make_config({"FOO": "bar"})
    assert find_by_tag(config, "local", "nonexistent") == []
