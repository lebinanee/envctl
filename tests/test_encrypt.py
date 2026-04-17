"""Tests for envctl.encrypt module."""

import pytest
from envctl.encrypt import (
    encrypt_value,
    decrypt_value,
    encrypt_profile,
    decrypt_profile,
    EncryptError,
    DecryptError,
)

PASSPHRASE = "super-secret-passphrase"


def test_encrypt_decrypt_roundtrip():
    original = "my_secret_value"
    token = encrypt_value(original, PASSPHRASE)
    assert token != original
    assert decrypt_value(token, PASSPHRASE) == original


def test_encrypt_produces_different_tokens():
    """Fernet uses random IV, so two encryptions differ."""
    v1 = encrypt_value("hello", PASSPHRASE)
    v2 = encrypt_value("hello", PASSPHRASE)
    assert v1 != v2


def test_decrypt_wrong_passphrase_raises():
    token = encrypt_value("secret", PASSPHRASE)
    with pytest.raises(DecryptError):
        decrypt_value(token, "wrong-passphrase")


def test_decrypt_invalid_token_raises():
    with pytest.raises(DecryptError):
        decrypt_value("not-a-valid-token", PASSPHRASE)


def test_encrypt_profile():
    profile = {"DB_PASS": "hunter2", "API_KEY": "abc123"}
    encrypted = encrypt_profile(profile, PASSPHRASE)
    assert set(encrypted.keys()) == set(profile.keys())
    for k, v in encrypted.items():
        assert v != profile[k]


def test_decrypt_profile_roundtrip():
    profile = {"DB_PASS": "hunter2", "API_KEY": "abc123"}
    encrypted = encrypt_profile(profile, PASSPHRASE)
    decrypted = decrypt_profile(encrypted, PASSPHRASE)
    assert decrypted == profile


def test_decrypt_profile_wrong_passphrase_raises():
    profile = {"KEY": "value"}
    encrypted = encrypt_profile(profile, PASSPHRASE)
    with pytest.raises(DecryptError):
        decrypt_profile(encrypted, "bad-pass")


def test_encrypt_empty_string():
    token = encrypt_value("", PASSPHRASE)
    assert decrypt_value(token, PASSPHRASE) == ""
