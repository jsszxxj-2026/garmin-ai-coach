from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict

from fastapi import HTTPException

from src.core.config import settings


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def _get_auth_secret() -> str:
    secret = settings.WECHAT_AUTH_SECRET or settings.GARMIN_CRED_ENCRYPTION_KEY or settings.WECHAT_MINI_SECRET
    if not secret:
        raise HTTPException(status_code=500, detail="鉴权配置缺失: WECHAT_AUTH_SECRET")
    return secret


def create_wechat_access_token(openid: str, expires_in_seconds: int) -> str:
    now = int(time.time())
    payload: Dict[str, Any] = {
        "openid": openid,
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    payload_raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload_encoded = _b64url_encode(payload_raw)
    signature = hmac.new(
        _get_auth_secret().encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{payload_encoded}.{_b64url_encode(signature)}"


def verify_wechat_access_token(token: str) -> Dict[str, Any]:
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效 token")

    expected_signature = hmac.new(
        _get_auth_secret().encode("utf-8"),
        payload_part.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    actual_signature = _b64url_decode(signature_part)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise HTTPException(status_code=401, detail="token 校验失败")

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=401, detail="token 解析失败")

    exp = payload.get("exp")
    openid = payload.get("openid")
    if not isinstance(exp, int) or not openid:
        raise HTTPException(status_code=401, detail="token 无效")
    if int(time.time()) >= exp:
        raise HTTPException(status_code=401, detail="token 已过期")
    return payload
