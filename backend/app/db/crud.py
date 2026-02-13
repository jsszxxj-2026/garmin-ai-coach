"""DB CRUD helpers.

This backend currently runs as a single-user service (Garmin credentials in env).
We still keep a `users` table so the schema stays multi-user capable.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Optional

from sqlalchemy.orm import Session, joinedload

from backend.app.db.models import (
    Activity,
    ActivityLap,
    DailyAnalysis,
    GarminDailySummary,
    GarminCredential,
    NotificationLog,
    SyncState,
    TrainingPlan,
    User,
    WechatUser,
)


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    try:
        return int(value)
    except Exception:
        return None


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        s = value.strip()
        if len(s) >= 10:
            s = s[:10]
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # Common formats: "YYYY-MM-DD HH:MM:SS" or ISO
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None
    return None


def get_or_create_user(db: Session, *, garmin_email: str) -> User:
    user = db.query(User).filter(User.garmin_email == garmin_email).one_or_none()
    if user:
        return user
    user = User(garmin_email=garmin_email)
    db.add(user)
    db.flush()
    return user


def get_or_create_wechat_user(db: Session, *, openid: str, unionid: Optional[str] = None) -> WechatUser:
    user = db.query(WechatUser).filter(WechatUser.openid == openid).one_or_none()
    if user:
        if unionid and user.unionid != unionid:
            user.unionid = unionid
        return user
    user = WechatUser(openid=openid, unionid=unionid)
    db.add(user)
    db.flush()
    return user


def get_garmin_credential(db: Session, *, wechat_user_id: int) -> Optional[GarminCredential]:
    return (
        db.query(GarminCredential)
        .filter(GarminCredential.wechat_user_id == wechat_user_id)
        .one_or_none()
    )


def upsert_garmin_credential(
    db: Session,
    *,
    wechat_user_id: int,
    garmin_email: str,
    garmin_password: str,
    is_cn: bool,
) -> GarminCredential:
    existing = (
        db.query(GarminCredential)
        .filter(GarminCredential.wechat_user_id == wechat_user_id)
        .filter(GarminCredential.garmin_email == garmin_email)
        .one_or_none()
    )
    fields = {
        "garmin_email": garmin_email,
        "garmin_password": garmin_password,
        "is_cn": 1 if is_cn else 0,
    }
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        return existing
    row = GarminCredential(wechat_user_id=wechat_user_id, **fields)
    db.add(row)
    db.flush()
    return row


def get_or_create_sync_state(db: Session, *, wechat_user_id: int) -> SyncState:
    state = (
        db.query(SyncState)
        .filter(SyncState.wechat_user_id == wechat_user_id)
        .one_or_none()
    )
    if state:
        return state
    state = SyncState(wechat_user_id=wechat_user_id)
    db.add(state)
    db.flush()
    return state


def log_notification(
    db: Session,
    *,
    wechat_user_id: int,
    event_type: str,
    event_key: str,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
) -> NotificationLog:
    row = NotificationLog(
        wechat_user_id=wechat_user_id,
        event_type=event_type,
        event_key=event_key,
        status=status,
        error_message=error_message,
    )
    db.add(row)
    return row


def get_cached_analysis(db: Session, *, user_id: int, analysis_date: date) -> Optional[DailyAnalysis]:
    return (
        db.query(DailyAnalysis)
        .filter(DailyAnalysis.user_id == user_id)
        .filter(DailyAnalysis.analysis_date == analysis_date)
        .one_or_none()
    )


def get_daily_summary_by_date(
    db: Session,
    *,
    user_id: int,
    summary_date: date,
) -> Optional[GarminDailySummary]:
    return (
        db.query(GarminDailySummary)
        .filter(GarminDailySummary.user_id == user_id)
        .filter(GarminDailySummary.summary_date == summary_date)
        .one_or_none()
    )


def get_activities_by_date(
    db: Session,
    *,
    user_id: int,
    activity_date: date,
) -> list[Activity]:
    return (
        db.query(Activity)
        .options(joinedload(Activity.laps))
        .filter(Activity.user_id == user_id)
        .filter(Activity.activity_date == activity_date)
        .order_by(Activity.start_time_local.asc(), Activity.id.asc())
        .all()
    )


def get_training_plans_in_range(
    db: Session,
    *,
    user_id: int,
    start_date: date,
    end_date: date,
) -> list[TrainingPlan]:
    return (
        db.query(TrainingPlan)
        .filter(TrainingPlan.user_id == user_id)
        .filter(TrainingPlan.plan_date >= start_date)
        .filter(TrainingPlan.plan_date <= end_date)
        .order_by(TrainingPlan.plan_date.asc(), TrainingPlan.id.asc())
        .all()
    )


def upsert_daily_summary(db: Session, *, user_id: int, health: dict[str, Any], summary_date: date) -> GarminDailySummary:
    existing = (
        db.query(GarminDailySummary)
        .filter(GarminDailySummary.user_id == user_id)
        .filter(GarminDailySummary.summary_date == summary_date)
        .one_or_none()
    )

    fields: dict[str, Any] = {
        "sleep_time_seconds": health.get("sleep_time_seconds"),
        "sleep_time_hours": health.get("sleep_time_hours"),
        "sleep_score": _to_int(health.get("sleep_score")),
        "deep_sleep_seconds": health.get("deep_sleep_seconds"),
        "rem_sleep_seconds": health.get("rem_sleep_seconds"),
        "light_sleep_seconds": health.get("light_sleep_seconds"),
        "awake_sleep_seconds": health.get("awake_sleep_seconds"),
        "recovery_quality_percent": health.get("recovery_quality_percent"),
        "resting_heart_rate": _to_int(health.get("resting_heart_rate")),
        "body_battery": _to_int(health.get("body_battery")),
        "body_battery_charged": _to_int(health.get("body_battery_charged")),
        "body_battery_drained": _to_int(health.get("body_battery_drained")),
        "average_stress_level": _to_int(health.get("average_stress_level")),
        "stress_qualifier": health.get("stress_qualifier"),
        "hrv_status": health.get("hrv_status") or health.get("hrvStatus"),
        "raw_json": health,
    }

    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        return existing

    row = GarminDailySummary(user_id=user_id, summary_date=summary_date, **fields)
    db.add(row)
    return row


def upsert_activities(db: Session, *, user_id: int, activities: Iterable[dict[str, Any]], fallback_date: date) -> list[Activity]:
    saved: list[Activity] = []

    for act in activities:
        if not isinstance(act, dict):
            continue

        garmin_activity_id = act.get("activity_id") or act.get("activityId") or act.get("activityID")
        metrics = act.get("metrics") if isinstance(act.get("metrics"), dict) else {}
        start_time_local_raw = act.get("start_time_local") or act.get("startTimeLocal")
        start_time_local = _parse_datetime(start_time_local_raw)

        activity_date = _parse_date(start_time_local) or fallback_date

        distance_km = metrics.get("distance_km")
        duration_seconds = metrics.get("duration_seconds")

        avg_pace_seconds: Optional[float] = None
        if isinstance(distance_km, (int, float)) and isinstance(duration_seconds, (int, float)) and float(distance_km) > 0:
            avg_pace_seconds = float(duration_seconds) / float(distance_km)

        existing: Optional[Activity] = None
        if garmin_activity_id is not None:
            existing = (
                db.query(Activity)
                .filter(Activity.user_id == user_id)
                .filter(Activity.garmin_activity_id == int(garmin_activity_id))
                .one_or_none()
            )

        if existing is None and start_time_local is not None:
            existing = (
                db.query(Activity)
                .filter(Activity.user_id == user_id)
                .filter(Activity.start_time_local == start_time_local)
                .filter(Activity.activity_date == activity_date)
                .one_or_none()
            )

        fields: dict[str, Any] = {
            "garmin_activity_id": int(garmin_activity_id) if garmin_activity_id is not None else None,
            "activity_date": activity_date,
            "type": act.get("type"),
            "name": act.get("name"),
            "start_time_local": start_time_local,
            "distance_km": float(distance_km) if isinstance(distance_km, (int, float)) else None,
            "duration_seconds": float(duration_seconds) if isinstance(duration_seconds, (int, float)) else None,
            "average_pace_seconds": avg_pace_seconds,
            "average_hr": _to_int(metrics.get("average_hr")),
            "max_hr": _to_int(metrics.get("max_hr")),
            "calories": _to_int(metrics.get("calories")),
            "average_cadence": _to_int(metrics.get("average_cadence")),
            "average_stride_length_cm": metrics.get("average_stride_length_cm"),
            "average_ground_contact_time_ms": _to_int(metrics.get("average_ground_contact_time_ms")),
            "average_vertical_oscillation_cm": metrics.get("average_vertical_oscillation_cm"),
            "average_vertical_ratio_percent": metrics.get("average_vertical_ratio_percent"),
            "raw_json": act,
        }

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            saved_activity = existing
        else:
            saved_activity = Activity(user_id=user_id, **fields)
            db.add(saved_activity)
            db.flush()

        # Upsert laps
        laps = act.get("laps") if isinstance(act.get("laps"), list) else []
        for lap in laps:
            if not isinstance(lap, dict):
                continue
            lap_index = lap.get("lap_index")
            if not isinstance(lap_index, int):
                try:
                    lap_index = int(lap_index)
                except Exception:
                    continue

            distance_km_lap = lap.get("distance_km")
            duration_seconds_lap = lap.get("duration_seconds")

            pace_seconds: Optional[float] = None
            if (
                isinstance(distance_km_lap, (int, float))
                and isinstance(duration_seconds_lap, (int, float))
                and float(distance_km_lap) > 0
            ):
                pace_seconds = float(duration_seconds_lap) / float(distance_km_lap)

            lap_existing = (
                db.query(ActivityLap)
                .filter(ActivityLap.activity_id == saved_activity.id)
                .filter(ActivityLap.lap_index == lap_index)
                .one_or_none()
            )
            lap_fields: dict[str, Any] = {
                "distance_km": float(distance_km_lap) if isinstance(distance_km_lap, (int, float)) else None,
                "duration_seconds": float(duration_seconds_lap) if isinstance(duration_seconds_lap, (int, float)) else None,
                "pace_seconds": pace_seconds,
                "average_hr": _to_int(lap.get("average_hr")),
                "max_hr": _to_int(lap.get("max_hr")),
                "cadence": _to_int(lap.get("cadence")),
                "stride_length_cm": lap.get("stride_length_cm"),
                "ground_contact_time_ms": _to_int(lap.get("ground_contact_time_ms")),
                "vertical_oscillation_cm": lap.get("vertical_oscillation_cm"),
                "vertical_ratio_percent": lap.get("vertical_ratio_percent"),
                "raw_json": lap,
            }
            if lap_existing:
                for k, v in lap_fields.items():
                    setattr(lap_existing, k, v)
            else:
                db.add(ActivityLap(activity_id=saved_activity.id, lap_index=lap_index, **lap_fields))

        saved.append(saved_activity)

    return saved


def upsert_training_plans(db: Session, *, user_id: int, plans: Iterable[dict[str, Any]]) -> int:
    count = 0

    for p in plans:
        if not isinstance(p, dict):
            continue
        plan_date_raw = p.get("date") or p.get("targetDate") or p.get("startDate") or p.get("calendarDate")
        plan_date = _parse_date(plan_date_raw)
        if not plan_date:
            continue

        workout_name = p.get("workoutName") or p.get("name") or p.get("title") or p.get("description")
        if not workout_name:
            continue
        workout_name = str(workout_name)
        description = p.get("description") or p.get("details")

        existing = (
            db.query(TrainingPlan)
            .filter(TrainingPlan.user_id == user_id)
            .filter(TrainingPlan.plan_date == plan_date)
            .filter(TrainingPlan.workout_name == workout_name)
            .one_or_none()
        )
        if existing:
            existing.description = str(description) if description is not None else None
            existing.raw_json = p
        else:
            db.add(
                TrainingPlan(
                    user_id=user_id,
                    plan_date=plan_date,
                    workout_name=workout_name,
                    description=str(description) if description is not None else None,
                    raw_json=p,
                )
            )
        count += 1

    return count


def save_analysis(
    db: Session,
    *,
    user_id: int,
    analysis_date: date,
    raw_data_summary_md: str,
    ai_advice_md: str,
    charts_json: Optional[dict[str, Any]],
    model_name: Optional[str],
    status: str,
    error_message: Optional[str],
) -> DailyAnalysis:
    existing = (
        db.query(DailyAnalysis)
        .filter(DailyAnalysis.user_id == user_id)
        .filter(DailyAnalysis.analysis_date == analysis_date)
        .one_or_none()
    )

    fields = {
        "raw_data_summary_md": raw_data_summary_md,
        "ai_advice_md": ai_advice_md,
        "charts_json": charts_json,
        "model_name": model_name,
        "status": status,
        "error_message": error_message,
        "generated_at": datetime.utcnow(),
    }

    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        return existing

    row = DailyAnalysis(user_id=user_id, analysis_date=analysis_date, **fields)
    db.add(row)
    return row
