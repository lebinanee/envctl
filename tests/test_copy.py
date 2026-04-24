"""Tests for envctl.copy module."""
import pytest
import json
import os
from envctl.config import Config
from envctl.copy import copy_keys, CopyError


def make_config(tmp_path, data):
    p = tmp_path / "envctl.json"
    p.write_text(json.dumps(data))
    return Config(str(p))


def _base(tmp_path):
    return make_config(tmp_path, {
        "active_env": "local",
        "profiles": {
            "local": {"DB": "localhost", "PORT": "5432"},
            "staging": {"DB": "staging-db"},
        }
    })


def test_copy_all_keys(tmp_path):
    cfg = _base(tmp_path)
    result = copy_keys(cfg, "local", "staging", overwrite=True)
    assert set(result["copied"]) == {"DB", "PORT"}
    assert cfg.get_profile("staging")["PORT"] == "5432"


def test_copy_specific_key(tmp_path):
    cfg = _base(tmp_path)
    result = copy_keys(cfg, "local", "staging", keys=["PORT"])
    assert result["copied"] == ["PORT"]
    assert cfg.get_profile("staging")["PORT"] == "5432"


def test_copy_skips_existing_without_overwrite(tmp_path):
    cfg = _base(tmp_path)
    result = copy_keys(cfg, "local", "staging")
    assert "DB" in result["skipped"]
    assert cfg.get_profile("staging")["DB"] == "staging-db"


def test_copy_missing_src_raises(tmp_path):
    cfg = _base(tmp_path)
    with pytest.raises(CopyError, match="Source profile"):
        copy_keys(cfg, "nope", "staging")


def test_copy_missing_dst_raises(tmp_path):
    cfg = _base(tmp_path)
    with pytest.raises(CopyError, match="Destination profile"):
        copy_keys(cfg, "local", "nope")


def test_copy_missing_key_raises(tmp_path):
    cfg = _base(tmp_path)
    with pytest.raises(CopyError, match="not found in source"):
        copy_keys(cfg, "local", "staging", keys=["MISSING"])


def test_copy_persists(tmp_path):
    cfg = _base(tmp_path)
    copy_keys(cfg, "local", "staging", keys=["PORT"])
    cfg2 = Config(cfg.path)
    assert cfg2.get_profile("staging")["PORT"] == "5432"


def test_copy_overwrite_updates_value(tmp_path):
    """Ensure overwrite=True replaces an existing key's value in the destination."""
    cfg = _base(tmp_path)
    # 'DB' exists in staging as 'staging-db'; local has 'localhost'
    result = copy_keys(cfg, "local", "staging", keys=["DB"], overwrite=True)
    assert "DB" in result["copied"]
    assert "DB" not in result.get("skipped", [])
    assert cfg.get_profile("staging")["DB"] == "localhost"
