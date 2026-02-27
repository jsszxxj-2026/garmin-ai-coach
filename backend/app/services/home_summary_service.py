from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.db.crud import get_or_create_user, get_garmin_credential
from backend.app.db.models import Activity, GarminDailySummary, WechatUser, User
from backend.app.services.gemini_service import GeminiService
from src.core.config import settings

logger = logging.getLogger(__name__)


class HomeSummaryService:
    def __init__(self, *, gemini: Optional[GeminiService] = None) -> None:
        self.gemini = gemini or GeminiService()

    def should_generate_ai_brief(self, *, run_count: int, sleep_days: int) -> bool:
        if run_count < 3 or sleep_days < 3:
            logger.info("[HomeSummary] Insufficient data; skip AI brief")
            return False

        gemini_key = settings.GEMINI_API_KEY
        if not gemini_key or not gemini_key.strip():
            logger.info("[HomeSummary] Gemini API key missing; skip AI brief")
            return False
        return True

    def build_latest_run(self) -> Dict[str, Any]:
        return {}

    def build_week_stats(self) -> Dict[str, Any]:
        return {}

    def build_month_stats(self) -> Dict[str, Any]:
        return {}

    def build_ai_brief(self) -> Dict[str, Any]:
        if not self.should_generate_ai_brief(run_count=0, sleep_days=0):
            return {}
        return {}

    def build_summary(
        self,
        *,
        db: Session,
        wechat_user_id: int,
        include_ai_brief: bool = True,
    ) -> Dict[str, Any]:
        wechat_user = db.query(WechatUser).filter(WechatUser.id == wechat_user_id).one_or_none()
        if not wechat_user:
            logger.warning(f"[HomeSummary] WechatUser {wechat_user_id} not found")
            return {"latest_run": None, "week_stats": None, "month_stats": None, "ai_brief": None, "updated_at": datetime.utcnow().isoformat()}
        
        credential = get_garmin_credential(db, wechat_user_id=wechat_user_id)
        if not credential:
            logger.warning(f"[HomeSummary] No Garmin credential for wechat_user {wechat_user_id}")
            return {"latest_run": None, "week_stats": None, "month_stats": None, "ai_brief": None, "updated_at": datetime.utcnow().isoformat()}
        
        # 临时方案：用 Garmin 邮箱查找对应的 User（同一 Garmin 账号）
        user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
        if not user:
            logger.warning(f"[HomeSummary] No User found for email {credential.garmin_email}")
            return {"latest_run": None, "week_stats": None, "month_stats": None, "ai_brief": None, "updated_at": datetime.utcnow().isoformat()}
        
        today = date.today()

        window_start = today - timedelta(days=29)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        runs_30 = self._get_running_activities(db, user_id=user.id, start_date=window_start, end_date=today)
        runs_week = self._get_running_activities(db, user_id=user.id, start_date=week_start, end_date=today)
        runs_month = self._get_running_activities(db, user_id=user.id, start_date=month_start, end_date=today)

        latest_run = self._build_latest_run(runs_30, window_start=window_start)
        week_stats = self._build_stats(runs_week)
        month_stats = self._build_stats(runs_month)

        sleep_days = self._count_sleep_days(db, user_id=user.id, start_date=window_start, end_date=today)
        run_count = len(runs_30)
        ai_brief: Dict[str, Optional[str]] | None = None
        if include_ai_brief:
            ai_brief = self._build_ai_brief(
                run_count=run_count,
                sleep_days=sleep_days,
                week_stats=week_stats,
                month_stats=month_stats,
            )

        return {
            "latest_run": latest_run,
            "week_stats": week_stats,
            "month_stats": month_stats,
            "ai_brief": ai_brief,
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _get_running_activities(
        self,
        db: Session,
        *,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> list[Activity]:
        rows = (
            db.query(Activity)
            .filter(Activity.user_id == user_id)
            .filter(Activity.activity_date >= start_date)
            .filter(Activity.activity_date <= end_date)
            .order_by(Activity.start_time_local.desc(), Activity.id.desc())
            .all()
        )
        return [row for row in rows if self._is_running(row)]

    @staticmethod
    def _is_running(activity: Activity) -> bool:
        t = (activity.type or "").lower()
        return "run" in t

    def _build_latest_run(self, activities: list[Activity], *, window_start: date) -> Optional[Dict[str, Any]]:
        for activity in activities:
            if activity.activity_date and activity.activity_date < window_start:
                continue
            if activity.distance_km is None or activity.duration_seconds is None:
                continue

            start_time = activity.start_time_local or datetime.combine(activity.activity_date, datetime.min.time())
            avg_pace_seconds = activity.average_pace_seconds
            if avg_pace_seconds is None and activity.distance_km > 0:
                avg_pace_seconds = float(activity.duration_seconds) / float(activity.distance_km)

            return {
                "start_time": start_time.isoformat(),
                "distance_km": round(float(activity.distance_km), 1),
                "intensity": self._format_intensity(activity.average_hr),
                "avg_pace": self._format_pace(avg_pace_seconds),
                "duration_min": int(round(float(activity.duration_seconds) / 60)),
            }
        return None

    @staticmethod
    def _format_intensity(avg_hr: Optional[int]) -> Optional[str]:
        if avg_hr is None:
            return None
        if avg_hr < 120:
            return "轻松"
        if avg_hr < 150:
            return "中等"
        return "较高"

    @staticmethod
    def _format_pace(pace_seconds: Optional[float]) -> Optional[str]:
        if pace_seconds is None or pace_seconds <= 0:
            return None
        mm = int(pace_seconds // 60)
        ss = int(round(pace_seconds % 60))
        if ss >= 60:
            ss = 0
            mm += 1
        return f"{mm}:{ss:02d}"

    @staticmethod
    def _build_stats(activities: list[Activity]) -> Dict[str, Any]:
        total_distance = 0.0
        total_duration = 0.0
        run_count = 0

        for activity in activities:
            if activity.distance_km is None or activity.duration_seconds is None:
                continue
            total_distance += float(activity.distance_km)
            total_duration += float(activity.duration_seconds)
            run_count += 1

        avg_speed_kmh = None
        if run_count >= 2 and total_distance >= 5 and total_duration > 0:
            avg_speed_kmh = round(total_distance / (total_duration / 3600.0), 1)

        return {
            "distance_km": round(total_distance, 1) if total_distance > 0 else 0,
            "avg_speed_kmh": avg_speed_kmh,
        }

    @staticmethod
    def _count_sleep_days(db: Session, *, user_id: int, start_date: date, end_date: date) -> int:
        rows = (
            db.query(GarminDailySummary)
            .filter(GarminDailySummary.user_id == user_id)
            .filter(GarminDailySummary.summary_date >= start_date)
            .filter(GarminDailySummary.summary_date <= end_date)
            .all()
        )
        count = 0
        for row in rows:
            if row.sleep_time_seconds is not None or row.sleep_time_hours is not None or row.sleep_score is not None:
                count += 1
        return count

    def _build_ai_brief(
        self,
        *,
        run_count: int,
        sleep_days: int,
        week_stats: Dict[str, Any],
        month_stats: Dict[str, Any],
    ) -> Dict[str, Optional[str]]:
        if not self.should_generate_ai_brief(run_count=run_count, sleep_days=sleep_days):
            return {"week": None, "month": None}

        try:
            return self.gemini.generate_home_summary_brief(
                week_stats=week_stats,
                month_stats=month_stats,
                run_count=run_count,
                sleep_days=sleep_days,
            )
        except Exception as e:
            logger.warning(f"[HomeSummary] AI brief failed: {e}")
            return {"week": None, "month": None}
