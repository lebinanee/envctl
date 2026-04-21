"""Tests for envctl.redact."""

from __future__ import annotations

import pytest

from envctl.redact import PLACEHOLDER, RedactError, redact_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeConfig:
    def __init__(self, profiles):
        self._profiles = profiles

    def get_profile(self, name):
        return self._profiles.get(name)


def make_config(data: dict) -> _FakeConfig:
    return _FakeConfig(data)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_redact_auto_detects_sensitive_key():
    cfg = make_config({"prod": {"DB_PASSWORD": "s3cr3t", "APP_NAME": "envctl"}})
    result = redact_profile(cfg, "prod")
    assert result.redacted["DB_PASSWORD"] == PLACEHOLDER
    assert result.redacted["APP_NAME"] == "envctl"
    assert "DB_PASSWORD" in result.redacted_keys
    assert "APP_NAME" in result.skipped_keys


def test_redact_explicit_key():
    cfg = make_config({"dev": {"APP_NAME": "envctl", "REGION": "us-east-1"}})
    result = redact_profile(cfg, "dev", keys=["REGION"], auto=False)
    assert result.redacted["REGION"] == PLACEHOLDER
    assert result.redacted["APP_NAME"] == "envctl"
    assert result.total_redacted == 1


def test_redact_no_auto_no_explicit_leaves_all_visible():
    cfg = make_config({"dev": {"SECRET_KEY": "abc", "PORT": "8080"}})
    result = redact_profile(cfg, "dev", keys=None, auto=False)
    assert result.total_redacted == 0
    assert result.redacted["SECRET_KEY"] == "abc"


def test_redact_missing_profile_raises():
    cfg = make_config({})
    with pytest.raises(RedactError, match="not found"):
        redact_profile(cfg, "ghost")


def test_redact_empty_profile():
    cfg = make_config({"staging": {}})
    result = redact_profile(cfg, "staging")
    assert result.redacted == {}
    assert result.total_redacted == 0


def test_redact_token_key_is_sensitive():
    cfg = make_config({"prod": {"API_TOKEN": "tok_xyz", "DEBUG": "false"}})
    result = redact_profile(cfg, "prod")
    assert result.redacted["API_TOKEN"] == PLACEHOLDER
    assert result.redacted["DEBUG"] == "false"


def test_redact_explicit_overrides_non_sensitive():
    cfg = make_config({"local": {"APP_ENV": "local"}})
    result = redact_profile(cfg, "local", keys=["APP_ENV"], auto=False)
    assert result.redacted["APP_ENV"] == PLACEHOLDER
    assert result.total_redacted == 1


def test_redact_result_keys_are_sorted():
    cfg = make_config({"prod": {"Z_SECRET": "z", "A_SECRET": "a", "M_TOKEN": "m"}})
    result = redact_profile(cfg, "prod")
    assert result.redacted_keys == sorted(result.redacted_keys)
