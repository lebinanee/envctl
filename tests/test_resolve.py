"""Tests for envctl.resolve."""
from __future__ import annotations

import pytest

from envctl.resolve import ResolveResult, resolve_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile(**kw: str):
    return dict(kw)


# ---------------------------------------------------------------------------
# Basic resolution
# ---------------------------------------------------------------------------

def test_resolve_no_references():
    result = resolve_profile(_profile(HOST="localhost", PORT="5432"))
    assert result.resolved["HOST"] == "localhost"
    assert result.resolved["PORT"] == "5432"
    assert not result.has_issues


def test_resolve_simple_reference():
    result = resolve_profile(_profile(BASE="http://example.com", URL="${BASE}/api"))
    assert result.resolved["URL"] == "http://example.com/api"
    assert not result.has_issues


def test_resolve_dollar_without_braces():
    result = resolve_profile(_profile(HOST="db", DSN="postgres://$HOST/mydb"))
    assert result.resolved["DSN"] == "postgres://db/mydb"


def test_resolve_chained_references():
    result = resolve_profile(
        _profile(SCHEME="https", HOST="example.com", BASE="${SCHEME}://${HOST}", URL="${BASE}/v1")
    )
    assert result.resolved["URL"] == "https://example.com/v1"
    assert not result.has_issues


def test_resolve_empty_profile():
    result = resolve_profile({})
    assert result.resolved == {}
    assert not result.has_issues


# ---------------------------------------------------------------------------
# Unresolved / external references
# ---------------------------------------------------------------------------

def test_resolve_unresolved_external_ref():
    result = resolve_profile(_profile(URL="${UNDEFINED}/path"))
    assert "UNDEFINED" in result.unresolved
    assert result.has_issues
    # Original placeholder preserved
    assert "${UNDEFINED}" in result.resolved["URL"]


def test_resolve_unresolved_listed_once():
    result = resolve_profile(_profile(A="${X}", B="${X}"))
    assert result.unresolved.count("X") == 1


# ---------------------------------------------------------------------------
# Cycle detection
# ---------------------------------------------------------------------------

def test_resolve_self_reference_detected_as_cycle():
    result = resolve_profile(_profile(A="${A}_suffix"))
    assert "A" in result.cycles
    assert result.has_issues


def test_resolve_mutual_cycle_detected():
    result = resolve_profile(_profile(A="${B}", B="${A}"))
    # Both A and B should appear in cycles
    assert set(result.cycles) == {"A", "B"}


# ---------------------------------------------------------------------------
# ResolveResult helpers
# ---------------------------------------------------------------------------

def test_resolve_result_has_issues_false_when_clean():
    r = ResolveResult(resolved={"K": "v"})
    assert not r.has_issues


def test_resolve_result_has_issues_true_with_unresolved():
    r = ResolveResult(unresolved=["MISSING"])
    assert r.has_issues


def test_resolve_result_has_issues_true_with_cycles():
    r = ResolveResult(cycles=["SELF"])
    assert r.has_issues
