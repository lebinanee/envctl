"""Tests for envctl.mask."""

import json
import pytest
from pathlib import Path
from envctl.config import Config
from envctl.mask import is_sensitive, mask_value, mask_profile, MaskError


@pytest.fixture
def make_config(tmp_path):
    def _make(profiles: dict) -> Config:
        p = tmp_path / "envctl.json"
        p.write_text(json.dumps({"active": "local", "profiles": profiles}))
        return Config(str(p))
    return _make


# --- is_sensitive ---

def test_is_sensitive_token():
    assert is_sensitive("API_TOKEN") is True

def test_is_sensitive_password():
    assert is_sensitive("DB_PASSWORD") is True

def test_is_sensitive_plain_key():
    assert is_sensitive("APP_ENV") is False

def test_is_sensitive_key_word():
    assert is_sensitive("SECRET_KEY") is True


# --- mask_value ---

def test_mask_value_long():
    assert mask_value("abcdefgh", 4) == "****efgh"

def test_mask_value_short():
    assert mask_value("ab", 4) == "**"

def test_mask_value_exact():
    assert mask_value("abcd", 4) == "****"


# --- mask_profile ---

def test_mask_profile_sensitive_masked(make_config):
    cfg = make_config({"local": {"API_TOKEN": "supersecret1234"}})
    result = mask_profile(cfg, "local")
    assert result["API_TOKEN"] == mask_value("supersecret1234")

def test_mask_profile_non_sensitive_plain(make_config):
    cfg = make_config({"local": {"APP_ENV": "production"}})
    result = mask_profile(cfg, "local")
    assert result["APP_ENV"] == "production"

def test_mask_profile_specific_keys(make_config):
    cfg = make_config({"local": {"APP_ENV": "production", "DB_PASSWORD": "s3cr3t"}})
    result = mask_profile(cfg, "local", keys=["DB_PASSWORD"])
    assert "APP_ENV" not in result
    assert result["DB_PASSWORD"] == mask_value("s3cr3t")

def test_mask_profile_missing_profile_raises(make_config):
    cfg = make_config({"local": {}})
    with pytest.raises(MaskError, match="Profile 'prod' not found"):
        mask_profile(cfg, "prod")

def test_mask_profile_missing_key_raises(make_config):
    cfg = make_config({"local": {"APP_ENV": "dev"}})
    with pytest.raises(MaskError, match="Key 'MISSING'"):
        mask_profile(cfg, "local", keys=["MISSING"])
