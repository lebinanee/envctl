import json
import time
import pytest
from pathlib import Path
from envctl.history import (
    record, get_history, clear_history, HistoryEntry, HistoryError
)


@pytest.fixture
def hist_file(tmp_path):
    return tmp_path / "history.json"


def test_record_creates_file(hist_file):
    record("local", "API_KEY", None, "abc", "set", path=hist_file)
    assert hist_file.exists()


def test_record_single_entry(hist_file):
    e = record("local", "API_KEY", None, "abc", "set", path=hist_file)
    assert isinstance(e, HistoryEntry)
    assert e.profile == "local"
    assert e.key == "API_KEY"
    assert e.new_value == "abc"
    assert e.action == "set"


def test_record_multiple_entries(hist_file):
    record("local", "A", None, "1", "set", path=hist_file)
    record("local", "A", "1", "2", "set", path=hist_file)
    entries = get_history(path=hist_file)
    assert len(entries) == 2


def test_entry_has_timestamp(hist_file):
    before = time.time()
    e = record("local", "X", None, "v", "set", path=hist_file)
    after = time.time()
    assert before <= e.timestamp <= after


def test_filter_by_profile(hist_file):
    record("local", "A", None, "1", "set", path=hist_file)
    record("prod", "B", None, "2", "set", path=hist_file)
    results = get_history(profile="local", path=hist_file)
    assert all(r.profile == "local" for r in results)
    assert len(results) == 1


def test_filter_by_key(hist_file):
    record("local", "FOO", None, "1", "set", path=hist_file)
    record("local", "BAR", None, "2", "set", path=hist_file)
    results = get_history(key="FOO", path=hist_file)
    assert len(results) == 1
    assert results[0].key == "FOO"


def test_invalid_action_raises(hist_file):
    with pytest.raises(HistoryError):
        record("local", "X", None, "v", "update", path=hist_file)


def test_delete_action(hist_file):
    e = record("prod", "SECRET", "old", None, "delete", path=hist_file)
    assert e.action == "delete"
    assert e.old_value == "old"
    assert e.new_value is None


def test_clear_history(hist_file):
    record("local", "A", None, "1", "set", path=hist_file)
    clear_history(path=hist_file)
    assert get_history(path=hist_file) == []
