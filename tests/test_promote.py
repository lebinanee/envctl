"""Tests for envctl.promote."""

import json
import pytest
from pathlib import Path
from envctl.config import Config
from envctl.promote import promote_keys, PromoteError


def make_config(tmp_path: Path) -> Config:
    data = {
        "active": "local",
        "profiles": {
            "local": {"DB_URL": "localhost", "DEBUG": "true"},
            "staging": {"DB_URL": "staging-db"},
            "production": {},
        },
    }
    p = tmp_path / "envctl.json"
    p.write_text(json.dumps(data))
    return Config(str(p))


def test_promote_all_keys(tmp_path):
    config = make_config(tmp_path)
    results = promote_keys(config, "local", "production")
    assert results["DB_URL"] == "promoted"
    assert results["DEBUG"] == "promoted"
    assert config.get_profile("production")["DB_URL"] == "localhost"


def test_promote_specific_key(tmp_path):
    config = make_config(tmp_path)
    results = promote_keys(config, "local", "production", keys=["DEBUG"])
    assert results == {"DEBUG": "promoted"}
    assert "DB_URL" not in config.get_profile("production")


def test_promote_skips_existing_without_overwrite(tmp_path):
    config = make_config(tmp_path)
    results = promote_keys(config, "local", "staging")
    assert results["DB_URL"] == "skipped"
    assert config.get_profile("staging")["DB_URL"] == "staging-db"


def test_promote_overwrites_when_flag_set(tmp_path):
    config = make_config(tmp_path)
    results = promote_keys(config, "local", "staging", overwrite=True)
    assert results["DB_URL"] == "overwritten"
    assert config.get_profile("staging")["DB_URL"] == "localhost"


def test_promote_same_profile_raises(tmp_path):
    config = make_config(tmp_path)
    with pytest.raises(PromoteError, match="must differ"):
        promote_keys(config, "local", "local")


def test_promote_invalid_src_raises(tmp_path):
    config = make_config(tmp_path)
    with pytest.raises(PromoteError, match="Source profile"):
        promote_keys(config, "nope", "staging")


def test_promote_missing_key_raises(tmp_path):
    config = make_config(tmp_path)
    with pytest.raises(PromoteError, match="not found"):
        promote_keys(config, "local", "staging", keys=["MISSING_KEY"])


def test_promote_persists_to_disk(tmp_path):
    config = make_config(tmp_path)
    promote_keys(config, "local", "production")
    reloaded = Config(config._path)
    assert reloaded.get_profile("production")["DEBUG"] == "true"
