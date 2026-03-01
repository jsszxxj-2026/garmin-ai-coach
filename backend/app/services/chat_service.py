from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.db.crud import (
    add_chat_message,
    get_activities_by_date,
    get_chat_messages,
    get_daily_summary_by_date,
    get_garmin_credential,
    get_or_create_user,
    get_training_plans_in_range,
    get_user_profile,
)
from backend.app.db.models import GarminCredential, User
from backend.app.services.data_processor import DataProcessor
from backend.app.services.garmin_client import GarminClient
from backend.app.services.gemini_service import GeminiService
from backend.app.utils.crypto import decrypt_text
from src.core.config import settings


logger = logging.getLogger(__name__)


# 聊天系统提示词（自然对话风格，不是分析报告）
CHAT_SYSTEM_INSTRUCTION = """你是一位专业的跑步教练和运动科学顾问，正在和用户聊天。

**你的风格**：
- 像朋友一样自然地聊天，不要写分析报告
- 说话活泼、有温度，可以用 Emoji，但不要滥用
- 回答简洁直接，不废话，不要每次都列出完整分析
- 可以称呼用户为“跑友”

**背景数据使用原则**：
- 系统会提供用户的 Garmin 运动数据作为背景参考
- 只在用户问到相关内容时才主动引用数据，不要每次都把所有数据列一遍
- 如果用户问的问题和跑步无关，正常回答就好，不要强行拉回跑步话题
- 当用户问到训练建议时，基于其实际数据给出个性化建议

**回复格式**：
- 说人话，不要写报告格式（不要“身体状态评估”“跑步表现分析”“训练建议”这种标题）
- 可以用加粗和列表突出重点，但不要每次都用固定框架
- 返回纯文本，不要包裹在 ```json``` 或 ```markdown``` 中
"""


class ChatService:
    def __init__(
        self,
        *,
        gemini: Optional[GeminiService] = None,
        processor: Optional[DataProcessor] = None,
    ) -> None:
        self.gemini = gemini or GeminiService()
        self.processor = processor or DataProcessor()

    def reply(
        self,
        *,
        db: Session,
        wechat_user_id: int,
        message: str,
    ) -> str:
        """
        处理用户聊天消息，返回 AI 教练的回复。

        Args:
            db: 数据库会话
            wechat_user_id: 微信用户 ID
            message: 用户消息

        Returns:
            AI 教练的回复文本
        """
        # 获取用户凭证
        credential = get_garmin_credential(db, wechat_user_id=wechat_user_id)
        if not credential:
            return "请先绑定 Garmin 账号，然后再来和我聊天吧！🏃‍♂️"

        # 获取 User
        user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
        if not user:
            return "用户不存在，请先绑定 Garmin 账号。"

        # 保存用户消息
        try:
            add_chat_message(
                db,
                wechat_user_id=wechat_user_id,
                role="user",
                content=message,
            )
            db.commit()
        except Exception as e:
            logger.warning(f"[Chat] Failed to save user message: {e}")

        # 构建上下文
        context = self._build_context(db, user.id, credential, message)

        # 打印完整提示词用于调试
        logger.info(f"[Chat] Full prompt for user {wechat_user_id}:\n{context}")

        try:
            reply = self.gemini.chat(context)
        except Exception as e:
            logger.warning(f"[Chat] Gemini failed: {e}")
            return "对话暂不可用，请稍后重试。"

        # 保存 AI 回复
        try:
            add_chat_message(
                db,
                wechat_user_id=wechat_user_id,
                role="assistant",
                content=reply,
            )
            db.commit()
        except Exception as e:
            logger.warning(f"[Chat] Failed to save assistant message: {e}")

        return reply

    def _build_context(
        self,
        db: Session,
        user_id: int,
        credential: GarminCredential,
        user_message: str,
    ) -> str:
        """构建聊天上下文"""
        today = date.today()
        sections = []

        # 1. 用户最近跑步数据（最近 7 天）
        recent_activities = []
        for i in range(7):
            target_date = today - timedelta(days=i)
            activities = get_activities_by_date(
                db,
                user_id=user_id,
                activity_date=target_date,
            )
            recent_activities.extend(activities)

        if recent_activities:
            sections.append("=== 用户最近跑步（近7天）===")
            for act in recent_activities[-5:]:  # 最近 5 条
                if act.distance_km and act.duration_seconds:
                    pace = ""
                    if act.distance_km > 0:
                        pace_seconds = act.duration_seconds / act.distance_km
                        pace_min = int(pace_seconds // 60)
                        pace_sec = int(pace_seconds % 60)
                        pace = f"{pace_min}:{pace_sec:02d}/km"
                    sections.append(
                        f"- {act.activity_date}: {act.distance_km}km, "
                        f"配速 {pace}, 心率 {act.average_hr or '-'} bpm"
                    )

        # 2. 今日身体状态
        today_summary = get_daily_summary_by_date(db, user_id=user_id, summary_date=today)
        if today_summary and today_summary.raw_json:
            raw = today_summary.raw_json
            sections.append("\n=== 用户今日身体状态 ===")
            if raw.get("body_battery") is not None:
                sections.append(f"- Body Battery: {raw.get('body_battery')}")
            if raw.get("resting_heart_rate") is not None:
                sections.append(f"- 静息心率: {raw.get('resting_heart_rate')} bpm")
            if raw.get("sleep_score") is not None:
                sections.append(f"- 睡眠分数: {raw.get('sleep_score')}")
            if raw.get("sleep_time_hours") is not None:
                sections.append(f"- 睡眠时长: {raw.get('sleep_time_hours')} 小时")
            if raw.get("average_stress_level") is not None:
                sections.append(f"- 压力等级: {raw.get('average_stress_level')}")

        # 3. 用户个人档案
        profile = get_user_profile(db, user_id=user_id, profile_date=today)
        if profile and profile.raw_json:
            raw = profile.raw_json
            sections.append("\n=== 用户个人档案 ===")
            if raw.get("vo2_max"):
                sections.append(f"- VO2Max: {raw.get('vo2_max')}")
            if raw.get("max_heart_rate"):
                sections.append(f"- 最大心率: {raw.get('max_heart_rate')} bpm")
            if raw.get("resting_heart_rate"):
                sections.append(f"- 静息心率: {raw.get('resting_heart_rate')} bpm")
            if raw.get("weight_kg"):
                sections.append(f"- 体重: {raw.get('weight_kg')} kg")
            if raw.get("training_status"):
                sections.append(f"- 训练状态: {raw.get('training_status')}")

        # 4. 未来训练计划（明天开始 7 天）
        tomorrow = today + timedelta(days=1)
        plans = get_training_plans_in_range(
            db,
            user_id=user_id,
            start_date=tomorrow,
            end_date=tomorrow + timedelta(days=6),
        )
        if plans:
            sections.append("\n=== 未来训练计划（未来7天）===")
            for plan in plans:
                sections.append(f"- {plan.plan_date}: {plan.workout_name}")

        # 5. 用户提问
        sections.append(f"\n=== 用户消息 ===\n{user_message}")

        # 组合完整提示词
        full_prompt = f"""{CHAT_SYSTEM_INSTRUCTION}

以下是用户的 Garmin 运动数据，作为背景参考（不需要每次都列举，只在相关时引用）：

{chr(10).join(sections)}

请自然地回复用户的消息。
"""

        return full_prompt

    @staticmethod
    def _today() -> date:
        return date.today()
