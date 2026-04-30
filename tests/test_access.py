"""Tests for envctl.access."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envctl.access import (
    AccessError,
    set_access,
    revoke_access,
    check_access,
    list_access,
)


def make_config(tmp_path):
    cfg = MagicMock()
    cfg.path = str(tmp_path / "config.json")
    cfg.list_profiles.return_value = ["local", "staging", "production"]
    return cfg


def test_set_access_creates_file(tmp_path):
    cfg = make_config(tmp_path)
    set_access(cfg, "local", "dev", ["DB_URL", "API_KEY"], "read")
    acl_file = tmp_path / ".envctl_access.json"
    assert acl_file.exists()
    data = json.loads(acl_file.read_text())
    assert data["local"]["dev"]["read"] == ["API_KEY", "DB_URL"]


def test_set_access_invalid_mode_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(AccessError, match="Invalid mode"):
        set_access(cfg, "local", "dev", ["DB_URL"], "execute")


def test_set_access_deduplicates_keys(tmp_path):
    cfg = make_config(tmp_path)
    set_access(cfg, "local", "dev", ["DB_URL", "DB_URL", "API_KEY"], "write")
    acl_file = tmp_path / ".envctl_access.json"
    data = json.loads(acl_file.read_text())
    assert data["local"]["dev"]["write"] == ["API_KEY", "DB_URL"]


def test_check_access_allowed(tmp_path):
    cfg = make_config(tmp_path)
    set_access(cfg, "local", "dev", ["SECRET"], "read")
    assert check_access(cfg, "local", "dev", "SECRET", "read") is True


def test_check_access_denied(tmp_path):
    cfg = make_config(tmp_path)
    set_access(cfg, "local", "dev", ["SECRET"], "read")
    assert check_access(cfg, "local", "dev", "OTHER", "read") is False


def test_check_access_wrong_mode(tmp_path):
    cfg = make_config(tmp_path)
    set_access(cfg, "local", "dev", ["SECRET"], "read")
    assert check_access(cfg, "local", "dev", "SECRET", "write") is False


def test_revoke_access_by_mode(tmp_path):
    cfg = make_config(tmp_path)
    set_access(cfg, "local", "dev", ["SECRET"], "read")
    result = revoke_access(cfg, "local", "dev", "read")
    assert result is True
    assert check_access(cfg, "local", "dev", "SECRET", "read") is False


def test_revoke_access_all_modes(tmp_path):
    cfg = make_config(tmp_path)
    set_access(cfg, "local", "dev", ["SECRET"], "read")
    set_access(cfg, "local", "dev", ["SECRET"], "write")
    result = revoke_access(cfg, "local", "dev", None)
    assert result is True
    assert list_access(cfg, "local") == {}


def test_revoke_nonexistent_returns_false(tmp_path):
    cfg = make_config(tmp_path)
    result = revoke_access(cfg, "local", "ghost", "read")
    assert result is False


def test_list_access_empty(tmp_path):
    cfg = make_config(tmp_path)
    assert list_access(cfg, "local") == {}


def test_list_access_multiple_roles(tmp_path):
    cfg = make_config(tmp_path)
    set_access(cfg, "staging", "admin", ["DB_PASS"], "write")
    set_access(cfg, "staging", "viewer", ["APP_URL"], "read")
    acl = list_access(cfg, "staging")
    assert "admin" in acl
    assert "viewer" in acl
