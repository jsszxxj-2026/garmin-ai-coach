from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.db.models import WechatUser
from backend.app.db.session import get_db
from backend.app.utils.auth import verify_wechat_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_wechat_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> WechatUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="未登录")

    payload = verify_wechat_access_token(credentials.credentials)
    openid = payload.get("openid")
    if not isinstance(openid, str) or not openid:
        raise HTTPException(status_code=401, detail="token 无效")

    user = db.query(WechatUser).filter(WechatUser.openid == openid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
