"""
Symmetric encryption for sensitive values (API keys, etc.).

Uses Fernet (AES-128-CBC + HMAC-SHA256) with a key derived from settings.secret_key.
The server secret_key must be consistent across restarts — if it changes, all
encrypted values become unreadable.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def _fernet() -> Fernet:
    from core.config import settings
    key_bytes = hashlib.sha256(settings.secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns a URL-safe token string."""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a token. Raises ValueError if token is invalid or key changed."""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Decryption failed — key may have changed") from e
