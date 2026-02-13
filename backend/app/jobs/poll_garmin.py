from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.db.crud import (
    get_or_create_sync_state,
    log_notification,
    get_garmin_credential,
)
from backend.app.db.models import WechatUser
from backend.app.services.report_service import ReportService
from backend.app.services.wechat_service import WechatService


logger = logging.getLogger(__name__)


def detect_new_data(sync_state: Dict[str, Any], latest: Dict[str, Any]) -> bool:
    if not sync_state or not latest:
        return False
    last_activity_id = sync_state.get("last_activity_id")
    last_summary_date = sync_state.get("last_summary_date")

    latest_activity_id = latest.get("latest_activity_id")
    latest_summary_date = latest.get("latest_summary_date")

    if latest_activity_id and latest_activity_id != last_activity_id:
        return True
    if latest_summary_date and latest_summary_date != last_summary_date:
        return True
    return False


def build_template_data(report_date: str, summary: str) -> Dict[str, Dict[str, str]]:
    return {
        "thing1": {"value": "AI 跑步日报"},
        "date2": {"value": report_date},
        "thing3": {"value": summary},
    }


def _build_latest_snapshot() -> Dict[str, Any]:
    now_date = datetime.now().date().isoformat()
    return {
        "latest_activity_id": None,
        "latest_summary_date": now_date,
    }


def poll_garmin_for_user(
    *,
    db: Session,
    wechat_user: WechatUser,
    report_service: ReportService,
    wechat_service: WechatService,
) -> None:
    credential = get_garmin_credential(db, wechat_user_id=wechat_user.id)
    if credential is None:
        return

    sync_state = get_or_create_sync_state(db, wechat_user_id=wechat_user.id)
    latest_snapshot = _build_latest_snapshot()

    if not detect_new_data(
        {
            "last_activity_id": sync_state.last_activity_id,
            "last_summary_date": sync_state.last_summary_date.isoformat() if sync_state.last_summary_date else None,
        },
        latest_snapshot,
    ):
        return

    analysis_date = latest_snapshot.get("latest_summary_date") or datetime.now().date().isoformat()

    result = report_service.build_daily_analysis(
        wechat_user_id=wechat_user.id,
        analysis_date=analysis_date,
        force_refresh=True,
        db=db,
    )

    sync_state.last_summary_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
    sync_state.last_poll_at = datetime.utcnow()
    db.flush()

    event_key = f"daily:{analysis_date}"
    try:
        summary = result.get("ai_advice") or "报告已生成"
        wechat_service.send_subscribe_message(
            openid=wechat_user.openid,
            data=build_template_data(analysis_date, summary[:30]),
        )
        log_notification(
            db,
            wechat_user_id=wechat_user.id,
            event_type="daily_report",
            event_key=event_key,
            status="sent",
        )
        db.commit()
    except Exception as e:
        db.rollback()
        log_notification(
            db,
            wechat_user_id=wechat_user.id,
            event_type="daily_report",
            event_key=event_key,
            status="error",
            error_message=str(e),
        )
        db.commit()
        logger.warning(f"[Poll] failed to send message: {e}")

    _ = result


def poll_garmin(db: Session) -> None:
    report_service = ReportService()
    wechat_service = WechatService()

    users = db.query(WechatUser).all()
    for user in users:
        try:
            poll_garmin_for_user(
                db=db,
                wechat_user=user,
                report_service=report_service,
                wechat_service=wechat_service,
            )
        except Exception as e:
            logger.warning(f"[Poll] failed for user {user.id}: {e}")
