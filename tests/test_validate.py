"""Tests for envctl.validate module."""

import pytest
from envctl.validate import (
    ValidationError,
    validate_key,
    validate_value,
    validate_pair,
    validate_profile,
)


# --- validate_key ---

def test_valid_keys():
    for key in ("FOO", "FOO_BAR", "_PRIVATE", "A1_B2"):
        validate_key(key)  # should not raise


def test_empty_key_raises():
    with pytest.raises(ValidationError, match="empty"):
        validate_key("")


def test_lowercase_key_raises():
    with pytest.raises(ValidationError, match="Invalid key"):
        validate_key("foo")


def test_key_starts_with_digit_raises():
    with pytest.raises(ValidationError, match="Invalid key"):
        validate_key("1FOO")


def test_key_with_space_raises():
    with pytest.raises(ValidationError, match="Invalid key"):
        validate_key("FOO BAR")


# --- validate_value ---

def test_valid_value():
    validate_value("hello world")  # should not raise
    validate_value("")             # empty string is fine


def test_value_with_null_byte_raises():
    with pytest.raises(ValidationError, match="null bytes"):
        validate_value("bad\x00value")


# --- validate_pair ---

def test_valid_pair():
    validate_pair("DATABASE_URL", "postgres://localhost/db")


def test_invalid_pair_key_propagates():
    with pytest.raises(ValidationError):
        validate_pair("bad-key", "value")


# --- validate_profile ---

def test_profile_all_valid():
    profile = {"HOST": "localhost", "PORT": "5432"}
    errors = validate_profile(profile)
    assert errors == []


def test_profile_with_errors():
    profile = {"good_key": "val", "ALSO_BAD": "v\x00al", "VALID": "ok"}
    errors = validate_profile(profile)
    assert len(errors) == 2


def test_profile_empty():
    assert validate_profile({}) == []
