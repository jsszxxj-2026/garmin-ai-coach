from __future__ import annotations

import base64
from typing import Optional

from cryptography.fernet import Fernet

from src.core.config import settings


def _normalize_key(raw_key: Optional[str]) -> bytes:
    if raw_key is None:
        raise ValueError("GARMIN_CRED_ENCRYPTION_KEY is required")

    key = raw_key.strip().encode("utf-8")
    try:
        decoded = base64.urlsafe_b64decode(key)
        if len(decoded) == 32:
            return base64.urlsafe_b64encode(decoded)
    except Exception:
        decoded = None

    if len(key) == 32:
        return base64.urlsafe_b64encode(key)

    raise ValueError("GARMIN_CRED_ENCRYPTION_KEY must be 32 bytes or base64-encoded 32 bytes")


def _get_fernet() -> Fernet:
    return Fernet(_normalize_key(settings.GARMIN_CRED_ENCRYPTION_KEY))


def encrypt_text(plain: str) -> str:
    if plain is None:
        raise ValueError("plain text is required")
    token = _get_fernet().encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(cipher: str) -> str:
    if cipher is None:
        raise ValueError("cipher text is required")
    plain = _get_fernet().decrypt(cipher.encode("utf-8"))
    return plain.decode("utf-8")
