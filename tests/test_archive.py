"""Tests for envctl.archive — create_archive and restore_archive."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from envctl.config import Config
from envctl.archive import ArchiveError, create_archive, restore_archive


@pytest.fixture()
def make_config(tmp_path):
    def _make(profiles: dict[str, dict[str, str]]) -> Config:
        cfg_file = tmp_path / "config.json"
        data = {"active_env": "local", "profiles": profiles}
        cfg_file.write_text(json.dumps(data))
        return Config(path=cfg_file)

    return _make


def test_create_archive_produces_zip(make_config, tmp_path):
    cfg = make_config({"local": {"KEY": "val"}, "prod": {"KEY": "prodval"}})
    dest = tmp_path / "archives"
    path = create_archive(cfg, dest)
    assert path.exists()
    assert path.suffix == ".zip"
    assert zipfile.is_zipfile(path)


def test_create_archive_contains_meta_and_profiles(make_config, tmp_path):
    cfg = make_config({"local": {"A": "1"}, "staging": {"B": "2"}})
    path = create_archive(cfg, tmp_path / "out", label="mybackup")
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert "meta.json" in names
        assert "profiles/local.json" in names
        assert "profiles/staging.json" in names
        meta = json.loads(zf.read("meta.json"))
        assert meta["label"] == "mybackup"
        assert set(meta["profiles"]) == {"local", "staging"}


def test_create_archive_raises_on_empty_profiles(make_config, tmp_path):
    cfg = make_config({})
    with pytest.raises(ArchiveError, match="No profiles"):
        create_archive(cfg, tmp_path / "out")


def test_restore_archive_imports_profiles(make_config, tmp_path):
    src = make_config({"local": {"X": "10"}, "prod": {"Y": "20"}})
    archive = create_archive(src, tmp_path / "arch")

    dst = make_config({})  # empty destination
    results = restore_archive(dst, archive)
    assert results["local"] == 1
    assert results["prod"] == 1
    assert dst.get_profile("local") == {"X": "10"}
    assert dst.get_profile("prod") == {"Y": "20"}


def test_restore_archive_skips_existing_without_overwrite(make_config, tmp_path):
    src = make_config({"local": {"KEY": "from_archive"}})
    archive = create_archive(src, tmp_path / "arch")

    dst = make_config({"local": {"KEY": "original"}})
    restore_archive(dst, archive, overwrite=False)
    assert dst.get_profile("local")["KEY"] == "original"


def test_restore_archive_overwrites_when_flag_set(make_config, tmp_path):
    src = make_config({"local": {"KEY": "from_archive"}})
    archive = create_archive(src, tmp_path / "arch")

    dst = make_config({"local": {"KEY": "original"}})
    restore_archive(dst, archive, overwrite=True)
    assert dst.get_profile("local")["KEY"] == "from_archive"


def test_restore_archive_missing_file_raises(make_config, tmp_path):
    cfg = make_config({})
    with pytest.raises(ArchiveError, match="not found"):
        restore_archive(cfg, tmp_path / "nonexistent.zip")


def test_restore_archive_invalid_zip_raises(make_config, tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip")
    cfg = make_config({})
    with pytest.raises(ArchiveError, match="Invalid zip"):
        restore_archive(cfg, bad)
