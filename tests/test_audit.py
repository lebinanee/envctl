"""Tests for the audit module."""

import json
import os
import pytest
from envctl.audit import AuditEntry, record, get_log, clear_log


@pytest.fixture
def audit_file(tmp_path):
    return str(tmp_path / "audit.json")


def test_record_creates_file(audit_file):
    entry = AuditEntry(action="set", env="local", key="FOO", new_value="bar")
    record(entry, path=audit_file)
    assert os.path.exists(audit_file)


def test_record_single_entry(audit_file):
    entry = AuditEntry(action="set", env="local", key="FOO", new_value="bar")
    record(entry, path=audit_file)
    log = get_log(audit_file)
    assert len(log) == 1
    assert log[0]["action"] == "set"
    assert log[0]["env"] == "local"
    assert log[0]["key"] == "FOO"
    assert log[0]["new_value"] == "bar"
    assert log[0]["old_value"] is None


def test_record_multiple_entries(audit_file):
    for i in range(3):
        record(AuditEntry("set", "staging", f"KEY_{i}", new_value=str(i)), path=audit_file)
    log = get_log(audit_file)
    assert len(log) == 3


def test_entry_has_timestamp(audit_file):
    entry = AuditEntry(action="delete", env="prod", key="SECRET", old_value="x")
    record(entry, path=audit_file)
    log = get_log(audit_file)
    assert "timestamp" in log[0]
    assert log[0]["timestamp"] != ""


def test_clear_log(audit_file):
    record(AuditEntry("set", "local", "A", new_value="1"), path=audit_file)
    clear_log(audit_file)
    assert get_log(audit_file) == []


def test_get_log_missing_file(audit_file):
    assert get_log(audit_file) == []


def test_to_dict_fields():
    entry = AuditEntry("sync", "staging", "DB_URL", old_value="old", new_value="new")
    d = entry.to_dict()
    assert d["action"] == "sync"
    assert d["old_value"] == "old"
    assert d["new_value"] == "new"
