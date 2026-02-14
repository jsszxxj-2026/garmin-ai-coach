"""SQLAlchemy ORM models for normalized GarminCoach storage."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from backend.app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    garmin_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    daily_summaries: Mapped[list[GarminDailySummary]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list[Activity]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    training_plans: Mapped[list[TrainingPlan]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    analyses: Mapped[list[DailyAnalysis]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class WechatUser(Base):
    __tablename__ = "wechat_users"
    __table_args__ = {"mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    unionid: Mapped[Optional[str]] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    garmin_credentials: Mapped[list[GarminCredential]] = relationship(
        back_populates="wechat_user",
        cascade="all, delete-orphan",
    )
    sync_states: Mapped[list[SyncState]] = relationship(
        back_populates="wechat_user",
        cascade="all, delete-orphan",
    )
    notification_logs: Mapped[list[NotificationLog]] = relationship(
        back_populates="wechat_user",
        cascade="all, delete-orphan",
    )
    home_summary: Mapped[Optional[HomeSummary]] = relationship(
        back_populates="wechat_user",
        cascade="all, delete-orphan",
        uselist=False,
    )


class GarminCredential(Base):
    __tablename__ = "garmin_credentials"
    __table_args__ = (
        UniqueConstraint("wechat_user_id", "garmin_email", name="uq_garmin_cred_user_email"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wechat_user_id: Mapped[int] = mapped_column(ForeignKey("wechat_users.id", ondelete="CASCADE"), nullable=False)

    garmin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    garmin_password: Mapped[str] = mapped_column(Text, nullable=False)
    is_cn: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    wechat_user: Mapped[WechatUser] = relationship(back_populates="garmin_credentials")


class SyncState(Base):
    __tablename__ = "sync_states"
    __table_args__ = (
        UniqueConstraint("wechat_user_id", name="uq_sync_state_wechat_user"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wechat_user_id: Mapped[int] = mapped_column(ForeignKey("wechat_users.id", ondelete="CASCADE"), nullable=False)

    last_activity_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_summary_date: Mapped[Optional[date]] = mapped_column(Date)
    last_poll_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    wechat_user: Mapped[WechatUser] = relationship(back_populates="sync_states")


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    __table_args__ = (
        UniqueConstraint("wechat_user_id", "event_type", "event_key", name="uq_notify_user_type_key"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wechat_user_id: Mapped[int] = mapped_column(ForeignKey("wechat_users.id", ondelete="CASCADE"), nullable=False)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_key: Mapped[str] = mapped_column(String(128), nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[Optional[str]] = mapped_column(String(32))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    wechat_user: Mapped[WechatUser] = relationship(back_populates="notification_logs")


class HomeSummary(Base):
    __tablename__ = "home_summaries"
    __table_args__ = (
        UniqueConstraint("wechat_user_id", name="uq_home_summary_wechat_user"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wechat_user_id: Mapped[int] = mapped_column(ForeignKey("wechat_users.id", ondelete="CASCADE"), nullable=False)

    latest_run_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    week_stats_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    month_stats_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    ai_brief_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    wechat_user: Mapped[WechatUser] = relationship(back_populates="home_summary")


class GarminDailySummary(Base):
    __tablename__ = "garmin_daily_summaries"
    __table_args__ = (
        UniqueConstraint("user_id", "summary_date", name="uq_daily_summary_user_date"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Sleep
    sleep_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    sleep_time_hours: Mapped[Optional[float]] = mapped_column(Float)
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer)
    deep_sleep_seconds: Mapped[Optional[float]] = mapped_column(Float)
    rem_sleep_seconds: Mapped[Optional[float]] = mapped_column(Float)
    light_sleep_seconds: Mapped[Optional[float]] = mapped_column(Float)
    awake_sleep_seconds: Mapped[Optional[float]] = mapped_column(Float)
    recovery_quality_percent: Mapped[Optional[float]] = mapped_column(Float)

    # Health
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery_charged: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery_drained: Mapped[Optional[int]] = mapped_column(Integer)
    average_stress_level: Mapped[Optional[int]] = mapped_column(Integer)
    stress_qualifier: Mapped[Optional[str]] = mapped_column(String(64))
    hrv_status: Mapped[Optional[str]] = mapped_column(String(64))

    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="daily_summaries")


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint("user_id", "garmin_activity_id", name="uq_activity_user_garmin_id"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    garmin_activity_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    activity_date: Mapped[Optional[date]] = mapped_column(Date)
    type: Mapped[Optional[str]] = mapped_column(String(64))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    start_time_local: Mapped[Optional[datetime]] = mapped_column(DateTime)

    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    average_pace_seconds: Mapped[Optional[float]] = mapped_column(Float)  # seconds / km

    average_hr: Mapped[Optional[int]] = mapped_column(Integer)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer)
    calories: Mapped[Optional[int]] = mapped_column(Integer)

    average_cadence: Mapped[Optional[int]] = mapped_column(Integer)
    average_stride_length_cm: Mapped[Optional[float]] = mapped_column(Float)
    average_ground_contact_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    average_vertical_oscillation_cm: Mapped[Optional[float]] = mapped_column(Float)
    average_vertical_ratio_percent: Mapped[Optional[float]] = mapped_column(Float)

    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="activities")
    laps: Mapped[list[ActivityLap]] = relationship(
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="ActivityLap.lap_index",
    )


class ActivityLap(Base):
    __tablename__ = "activity_laps"
    __table_args__ = (
        UniqueConstraint("activity_id", "lap_index", name="uq_activity_lap_activity_index"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)

    lap_index: Mapped[int] = mapped_column(Integer, nullable=False)

    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    pace_seconds: Mapped[Optional[float]] = mapped_column(Float)  # seconds / km

    average_hr: Mapped[Optional[int]] = mapped_column(Integer)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer)

    cadence: Mapped[Optional[int]] = mapped_column(Integer)
    stride_length_cm: Mapped[Optional[float]] = mapped_column(Float)
    ground_contact_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    vertical_oscillation_cm: Mapped[Optional[float]] = mapped_column(Float)
    vertical_ratio_percent: Mapped[Optional[float]] = mapped_column(Float)

    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    activity: Mapped[Activity] = relationship(back_populates="laps")


class TrainingPlan(Base):
    __tablename__ = "training_plans"
    __table_args__ = (
        UniqueConstraint("user_id", "plan_date", "workout_name", name="uq_plan_user_date_name"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)

    workout_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="training_plans")


class DailyAnalysis(Base):
    __tablename__ = "daily_analyses"
    __table_args__ = (
        UniqueConstraint("user_id", "analysis_date", name="uq_analysis_user_date"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)

    raw_data_summary_md: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    ai_advice_md: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    charts_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    model_name: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="success")
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="analyses")
