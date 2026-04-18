"""Tests for envctl.import_ module."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envctl.import_ import parse_dotenv, import_into_profile, ImportError as EnvImportError


@pytest.fixture
def dotenv_file(tmp_path):
    def _make(content):
        f = tmp_path / ".env"
        f.write_text(content)
        return str(f)
    return _make


def make_config(profile_data=None):
    cfg = MagicMock()
    cfg.get_profile = lambda env: dict(profile_data or {})
    cfg.set_var = MagicMock()
    cfg.save = MagicMock()
    return cfg


def test_parse_simple(dotenv_file):
    path = dotenv_file("FOO=bar\nBAZ=qux\n")
    assert parse_dotenv(path) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_skips_comments_and_blanks(dotenv_file):
    path = dotenv_file("# comment\n\nFOO=bar\n")
    assert parse_dotenv(path) == {"FOO": "bar"}


def test_parse_strips_quotes(dotenv_file):
    path = dotenv_file('FOO="hello world"\nBAR=\'test\'\n')
    assert parse_dotenv(path) == {"FOO": "hello world", "BAR": "test"}


def test_parse_missing_file():
    with pytest.raises(EnvImportError, match="File not found"):
        parse_dotenv("/nonexistent/.env")


def test_parse_invalid_line(dotenv_file):
    path = dotenv_file("NOTAVALIDLINE\n")
    with pytest.raises(EnvImportError, match="Invalid format"):
        parse_dotenv(path)


def test_parse_invalid_key(dotenv_file):
    path = dotenv_file("lowercase=value\n")
    with pytest.raises(EnvImportError, match="Validation error"):
        parse_dotenv(path)


def test_import_adds_new_vars(dotenv_file):
    path = dotenv_file("FOO=bar\n")
    cfg = make_config()
    summary = import_into_profile(cfg, "local", path)
    assert "FOO" in summary["added"]
    cfg.set_var.assert_called_once_with("local", "FOO", "bar")


def test_import_skips_existing_without_overwrite(dotenv_file):
    path = dotenv_file("FOO=bar\n")
    cfg = make_config({"FOO": "old"})
    summary = import_into_profile(cfg, "local", path, overwrite=False)
    assert "FOO" in summary["skipped"]
    cfg.set_var.assert_not_called()


def test_import_overwrites_when_flag_set(dotenv_file):
    path = dotenv_file("FOO=bar\n")
    cfg = make_config({"FOO": "old"})
    summary = import_into_profile(cfg, "local", path, overwrite=True)
    assert "FOO" in summary["updated"]
    cfg.set_var.assert_called_once()


def test_import_dry_run_does_not_save(dotenv_file):
    path = dotenv_file("FOO=bar\n")
    cfg = make_config()
    summary = import_into_profile(cfg, "local", path, dry_run=True)
    assert "FOO" in summary["added"]
    cfg.save.assert_not_called()
    cfg.set_var.assert_not_called()
