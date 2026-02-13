from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.db.crud import (
    get_cached_analysis,
    get_training_plans_in_range,
    get_or_create_user,
)
from backend.app.services.gemini_service import GeminiService
from src.core.config import settings


logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, *, gemini: Optional[GeminiService] = None) -> None:
        self.gemini = gemini or GeminiService()

    def reply(self, *, db: Session, message: str) -> str:
        user = get_or_create_user(db, garmin_email=settings.GARMIN_EMAIL)
        latest = get_cached_analysis(db, user_id=user.id, analysis_date=self._today())
        plans = get_training_plans_in_range(
            db,
            user_id=user.id,
            start_date=self._today(),
            end_date=self._today(),
        )

        plan_text = "\n".join([p.workout_name for p in plans]) if plans else "暂无计划"
        context = "\n".join(
            [
                "你是跑步教练，请根据用户提问回答，并提示明日训练计划。",
                f"用户问题: {message}",
                f"今日报告摘要: {latest.ai_advice_md if latest else '暂无'}",
                f"明日计划: {plan_text}",
            ]
        )

        try:
            return self.gemini.analyze_training(context)
        except Exception as e:
            logger.warning(f"[Chat] Gemini failed: {e}")
            return "对话暂不可用，请稍后重试。"

    @staticmethod
    def _today():
        from datetime import date

        return date.today()
