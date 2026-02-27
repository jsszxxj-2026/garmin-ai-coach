from __future__ import annotations

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.crud import (
    get_garmin_credential,
    get_or_create_wechat_user,
    upsert_garmin_credential,
)
from backend.app.db.models import WechatUser
from backend.app.db.session import get_db, get_sessionmaker
from backend.app.deps.auth import get_current_wechat_user
from backend.app.services.chat_service import ChatService
from backend.app.services.garmin_client import GarminClient
from backend.app.services.report_service import ReportService
from backend.app.utils.auth import create_wechat_access_token
from backend.app.utils.crypto import encrypt_text
from src.core.config import settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wechat", tags=["wechat"])


class WechatLoginRequest(BaseModel):
    code: str


class WechatLoginResponse(BaseModel):
    openid: str
    unionid: Optional[str] = None
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class GarminBindRequest(BaseModel):
    garmin_email: str
    garmin_password: str
    is_cn: bool = False


class GarminBindResponse(BaseModel):
    bound: bool
    backfill_started: bool = False
    backfill_days: int = 0


class GarminProfileResponse(BaseModel):
    openid: str
    has_binding: bool
    garmin_email: Optional[str] = None
    is_cn: Optional[bool] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def _run_initial_backfill(wechat_user_id: int, days: int) -> None:
    db = get_sessionmaker()()
    try:
        report_service = ReportService()
        result = report_service.sync_recent_history(
            wechat_user_id=wechat_user_id,
            days=days,
            db=db,
        )
        logger.info(f"[Backfill] completed for wechat_user_id={wechat_user_id}: {result}")
    except Exception as e:
        logger.warning(f"[Backfill] failed for wechat_user_id={wechat_user_id}: {e}")
    finally:
        db.close()


def _wechat_code_to_session(code: str) -> dict:
    if not settings.WECHAT_MINI_APPID or not settings.WECHAT_MINI_SECRET:
        raise HTTPException(status_code=500, detail="微信小程序配置缺失")

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_MINI_APPID,
        "secret": settings.WECHAT_MINI_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }

    with httpx.Client(timeout=10) as client:
        resp = client.get(url, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="微信服务请求失败")

    data = resp.json()
    if data.get("errcode"):
        raise HTTPException(status_code=400, detail=f"微信登录失败: {data.get('errmsg')}")
    if "openid" not in data:
        raise HTTPException(status_code=400, detail="微信登录失败: 未返回 openid")
    return data


@router.post("/login", response_model=WechatLoginResponse)
def wechat_login(payload: WechatLoginRequest, db: Session = Depends(get_db)) -> WechatLoginResponse:
    data = _wechat_code_to_session(payload.code)
    openid = data.get("openid")
    unionid = data.get("unionid")

    get_or_create_wechat_user(db, openid=openid, unionid=unionid)
    db.commit()
    expires_in = max(int(settings.WECHAT_ACCESS_TOKEN_EXPIRES_SECONDS), 3600)
    access_token = create_wechat_access_token(openid=openid, expires_in_seconds=expires_in)
    return WechatLoginResponse(
        openid=openid,
        unionid=unionid,
        access_token=access_token,
        expires_in=expires_in,
    )


@router.post("/bind-garmin", response_model=GarminBindResponse)
def bind_garmin(
    payload: GarminBindRequest,
    background_tasks: BackgroundTasks,
    current_user: WechatUser = Depends(get_current_wechat_user),
    db: Session = Depends(get_db),
) -> GarminBindResponse:
    if not payload.garmin_email or not payload.garmin_password:
        raise HTTPException(status_code=400, detail="Garmin 账号或密码为空")

    existing_credential = get_garmin_credential(db, wechat_user_id=current_user.id)

    try:
        GarminClient(email=payload.garmin_email, password=payload.garmin_password, is_cn=payload.is_cn)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Garmin 登录失败: {str(e)}")

    encrypted_password = encrypt_text(payload.garmin_password)
    upsert_garmin_credential(
        db,
        wechat_user_id=current_user.id,
        garmin_email=payload.garmin_email,
        garmin_password=encrypted_password,
        is_cn=payload.is_cn,
    )
    db.commit()

    backfill_days = max(int(settings.INITIAL_BIND_BACKFILL_DAYS), 0)
    should_backfill = existing_credential is None and backfill_days > 0
    if should_backfill:
        background_tasks.add_task(_run_initial_backfill, current_user.id, backfill_days)

    return GarminBindResponse(
        bound=True,
        backfill_started=should_backfill,
        backfill_days=backfill_days if should_backfill else 0,
    )


@router.post("/unbind-garmin")
def unbind_garmin(
    current_user: WechatUser = Depends(get_current_wechat_user),
    db: Session = Depends(get_db),
) -> dict:
    credential = get_garmin_credential(db, wechat_user_id=current_user.id)
    if credential is None:
        return {"bound": False}
    db.delete(credential)
    db.commit()
    return {"bound": False}


@router.get("/profile", response_model=GarminProfileResponse)
def get_profile(
    current_user: WechatUser = Depends(get_current_wechat_user),
    db: Session = Depends(get_db),
) -> GarminProfileResponse:
    credential = get_garmin_credential(db, wechat_user_id=current_user.id)
    if credential is None:
        return GarminProfileResponse(openid=current_user.openid, has_binding=False)
    return GarminProfileResponse(
        openid=current_user.openid,
        has_binding=True,
        garmin_email=credential.garmin_email,
        is_cn=bool(credential.is_cn),
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    _: WechatUser = Depends(get_current_wechat_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    service = ChatService()
    reply = service.reply(db=db, message=payload.message)
    return ChatResponse(reply=reply)
