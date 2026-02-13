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
