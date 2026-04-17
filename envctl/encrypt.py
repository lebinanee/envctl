"""Encryption utilities for securing environment variable values."""

import base64
import hashlib
import os
from cryptography.fernet import Fernet, InvalidToken


class EncryptError(Exception):
    pass


class DecryptError(Exception):
    pass


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte Fernet-compatible key from a passphrase."""
    digest = hashlib.sha256(passphrase.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet(passphrase: str) -> Fernet:
    return Fernet(_derive_key(passphrase))


def encrypt_value(value: str, passphrase: str) -> str:
    """Encrypt a plaintext value and return a base64 token string."""
    try:
        f = get_fernet(passphrase)
        token = f.encrypt(value.encode())
        return token.decode()
    except Exception as e:
        raise EncryptError(f"Encryption failed: {e}") from e


def decrypt_value(token: str, passphrase: str) -> str:
    """Decrypt a token string and return the original plaintext."""
    try:
        f = get_fernet(passphrase)
        return f.decrypt(token.encode()).decode()
    except InvalidToken:
        raise DecryptError("Decryption failed: invalid token or wrong passphrase.")
    except Exception as e:
        raise DecryptError(f"Decryption failed: {e}") from e


def encrypt_profile(profile: dict, passphrase: str) -> dict:
    """Return a new dict with all values encrypted."""
    return {k: encrypt_value(v, passphrase) for k, v in profile.items()}


def decrypt_profile(profile: dict, passphrase: str) -> dict:
    """Return a new dict with all values decrypted."""
    return {k: decrypt_value(v, passphrase) for k, v in profile.items()}
