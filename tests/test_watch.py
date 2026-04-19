"""Tests for envctl.watch."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from envctl.config import Config
from envctl.watch import WatchError, WatchEvent, watch_profile


@pytest.fixture
def tmp_cfg(tmp_path):
    p = tmp_path / "envctl.json"
    data = {
        "active": "local",
        "profiles": {
            "local": {"DB_URL": "sqlite:///dev.db", "DEBUG": "true"},
        },
    }
    p.write_text(json.dumps(data))
    return Config(str(p))


def test_watch_error_on_missing_profile(tmp_cfg):
    events = []
    with pytest.raises(WatchError, match="prod"):
        watch_profile(tmp_cfg, "prod", events.append, interval=0, max_cycles=1)


def test_watch_no_changes_emits_no_event(tmp_cfg):
    events = []
    with patch("time.sleep"):
        watch_profile(tmp_cfg, "local", events.append, interval=0, max_cycles=2)
    assert events == []


def test_watch_detects_added_key(tmp_cfg, tmp_path):
    cfg_path = tmp_path / "envctl.json"
    events = []
    call_count = 0

    def _reload_and_add():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            data = json.loads(cfg_path.read_text())
            data["profiles"]["local"]["NEW_KEY"] = "hello"
            cfg_path.write_text(json.dumps(data))

    with patch("time.sleep", side_effect=lambda _: _reload_and_add()):
        watch_profile(tmp_cfg, "local", events.append, interval=0, max_cycles=2)

    assert len(events) == 1
    assert "NEW_KEY" in events[0].added


def test_watch_detects_removed_key(tmp_cfg, tmp_path):
    cfg_path = tmp_path / "envctl.json"
    events = []
    call_count = 0

    def _remove_key():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            data = json.loads(cfg_path.read_text())
            del data["profiles"]["local"]["DEBUG"]
            cfg_path.write_text(json.dumps(data))

    with patch("time.sleep", side_effect=lambda _: _remove_key()):
        watch_profile(tmp_cfg, "local", events.append, interval=0, max_cycles=2)

    assert any("DEBUG" in e.removed for e in events)


def test_event_summary_no_changes():
    e = WatchEvent(profile="local")
    assert e.summary() == "no changes"
    assert not e.has_changes()


def test_event_summary_with_changes():
    e = WatchEvent(profile="local", added={"A": "1"}, changed={"B": ("old", "new")})
    assert "+1 added" in e.summary()
    assert "~1 changed" in e.summary()
    assert e.has_changes()
