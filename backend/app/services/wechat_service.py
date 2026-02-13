from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from src.core.config import settings


logger = logging.getLogger(__name__)


class WechatService:
    def __init__(self) -> None:
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def get_access_token(self) -> str:
        if not settings.WECHAT_MINI_APPID or not settings.WECHAT_MINI_SECRET:
            raise RuntimeError("微信小程序配置缺失")

        now = time.time()
        if self._cached_token and now < self._token_expires_at:
            return self._cached_token

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": settings.WECHAT_MINI_APPID,
            "secret": settings.WECHAT_MINI_SECRET,
        }

        with httpx.Client(timeout=10) as client:
            resp = client.get(url, params=params)

        if resp.status_code != 200:
            raise RuntimeError("微信 token 获取失败")

        data = resp.json()
        token = data.get("access_token")
        expires_in = data.get("expires_in")
        if not token:
            raise RuntimeError(f"微信 token 获取失败: {data.get('errmsg')}")

        ttl = settings.WECHAT_TOKEN_CACHE_SECONDS
        if isinstance(expires_in, int) and expires_in > 0:
            ttl = min(ttl, max(expires_in - 60, 0))

        self._cached_token = token
        self._token_expires_at = now + ttl
        return token

    def send_subscribe_message(
        self,
        *,
        openid: str,
        data: Dict[str, Any],
        page: Optional[str] = None,
    ) -> None:
        token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}"

        payload = {
            "touser": openid,
            "template_id": settings.WECHAT_SUBSCRIBE_TEMPLATE_ID,
            "page": page or settings.WECHAT_SUBSCRIBE_PAGE,
            "data": data,
        }

        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload)

        if resp.status_code != 200:
            raise RuntimeError("微信消息发送失败")

        result = resp.json()
        if result.get("errcode") not in (0, None):
            raise RuntimeError(f"微信消息发送失败: {result.get('errmsg')}")
