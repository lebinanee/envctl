"""Tests for envctl.export module."""

import os
import pytest
from unittest.mock import MagicMock
from envctl.export import render, export_to_file, ExportError


def make_config(profile_data):
    cfg = MagicMock()
    cfg.get_profile = lambda env: dict(profile_data.get(env, {}))
    return cfg


def test_render_dotenv():
    out = render({"FOO": "bar", "BAZ": "qux"}, fmt="dotenv")
    assert 'BAZ="qux"' in out
    assert 'FOO="bar"' in out


def test_render_shell():
    out = render({"FOO": "bar"}, fmt="shell")
    assert out.strip() == 'export FOO="bar"'


def test_render_escapes_quotes():
    out = render({"MSG": 'say "hi"'}, fmt="dotenv")
    assert 'MSG="say \\"hi\\""' in out


def test_render_empty():
    assert render({}) == ""


def test_render_unsupported_format():
    with pytest.raises(ExportError, match="Unsupported format"):
        render({"A": "1"}, fmt="json")


def test_export_to_file(tmp_path):
    cfg = make_config({"local": {"KEY": "value"}})
    out = tmp_path / ".env"
    export_to_file(cfg, "local", str(out))
    content = out.read_text()
    assert 'KEY="value"' in content


def test_export_no_overwrite_raises(tmp_path):
    cfg = make_config({"local": {"KEY": "value"}})
    out = tmp_path / ".env"
    out.write_text("existing")
    with pytest.raises(ExportError, match="already exists"):
        export_to_file(cfg, "local", str(out))


def test_export_overwrite(tmp_path):
    cfg = make_config({"local": {"KEY": "new"}})
    out = tmp_path / ".env"
    out.write_text("old")
    export_to_file(cfg, "local", str(out), overwrite=True)
    assert 'KEY="new"' in out.read_text()


def test_export_shell_format(tmp_path):
    cfg = make_config({"staging": {"PORT": "8080"}})
    out = tmp_path / "env.sh"
    export_to_file(cfg, "staging", str(out), fmt="shell")
    assert 'export PORT="8080"' in out.read_text()
