import pytest
from unittest.mock import MagicMock
from envctl.lint import lint_profile, lint_all_profiles, LintError, LintIssue


def make_config(profiles: dict) -> MagicMock:
    cfg = MagicMock()
    cfg.data = {"profiles": profiles}
    return cfg


def test_lint_clean_profile():
    cfg = make_config({"local": {"API_KEY": "abc123", "PORT": "8080"}})
    issues = lint_profile(cfg, "local")
    assert issues == []


def test_lint_empty_value_raises_error():
    cfg = make_config({"local": {"API_KEY": ""}})
    issues = lint_profile(cfg, "local")
    assert any(i.severity == "error" and "empty" in i.message for i in issues)


def test_lint_blank_value_raises_error():
    cfg = make_config({"local": {"API_KEY": "   "}})
    issues = lint_profile(cfg, "local")
    assert any(i.severity == "error" for i in issues)


def test_lint_suspicious_pattern_warning():
    cfg = make_config({"local": {"SECRET": "CHANGEME"}})
    issues = lint_profile(cfg, "local")
    assert any(i.severity == "warning" and "CHANGEME" in i.message for i in issues)


def test_lint_todo_pattern():
    cfg = make_config({"staging": {"DB_URL": "TODO: set this"}})
    issues = lint_profile(cfg, "staging")
    assert any("TODO" in i.message for i in issues)


def test_lint_long_value_warning():
    cfg = make_config({"local": {"BIG": "x" * 501}})
    issues = lint_profile(cfg, "local")
    assert any("long" in i.message for i in issues)


def test_lint_missing_profile_raises():
    cfg = make_config({})
    with pytest.raises(LintError, match="not found"):
        lint_profile(cfg, "ghost")


def test_lint_all_profiles():
    cfg = make_config({
        "local": {"KEY": "value"},
        "prod": {"KEY": "PLACEHOLDER"},
    })
    results = lint_all_profiles(cfg)
    assert "local" in results
    assert "prod" in results
    assert results["local"] == []
    assert any("PLACEHOLDER" in i.message for i in results["prod"])


def test_lint_issue_str():
    issue = LintIssue("local", "KEY", "warning", "some message")
    assert "WARNING" in str(issue)
    assert "local/KEY" in str(issue)
    assert "some message" in str(issue)


def test_lint_custom_suspicious_patterns():
    cfg = make_config({"local": {"TOKEN": "my_secret_REPLACE_ME"}})
    issues = lint_profile(cfg, "local", suspicious=["REPLACE_ME"])
    assert any("REPLACE_ME" in i.message for i in issues)
