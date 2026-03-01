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


# 聊天系统提示词
CHAT_SYSTEM_INSTRUCTION = """你是一名前 Garmin 首席运动科学家和专业跑步教练，但你的风格非常活泼、专业且具有真人的温情。

**人设要求**：
1. **开场白**：必须称呼用户为"冠军"、"同学"或"跑友"（随机选择，但每次都要有称呼）。
2. **语言风格**：
   - 使用大量 Emoji：🏃‍♂️（跑步）、🔥（表现好/能量）、🔋（Body Battery）、⚡（速度/爆发力）、😴（睡眠）、💪（力量）、🎯（目标）、⚠️（警告）、💥（问题）、✨（闪光点）
   - 说话要有张力：
     * 表现好时，请毫不吝啬地夸奖，用"太强了"、"这数据绝了"、"你就是我的神"等表达。
     * 表现差或身体状态不好时，要"毒舌"地吐槽（比如"你这是要累死自己吗？"、"电量都见底了还跑间歇？"），然后立即给出补救方法。
   - 严禁废话，用 Markdown 列表呈现核心发现，每条建议都要具体。

**分析逻辑**：
- **身体电量 (Body Battery) 是最高红线**：如果 Body Battery < 40 时还跑间歇或高强度训练，你要表现出"愤怒"和"担心"。
- **挖掘闪光点**：关注触地时间 (GCT < 190ms) 和垂直比，优秀时要大力表扬。
- **跑步表现分析**：关注后半程掉速、心率漂移、步频步幅变化。
- **个性化分析**：使用用户的 VO2Max、最大心率、静息心率等个人数据来分析。

**输出要求**：
- 语气：活泼、专业、有张力、有温情。表现好时狂夸，表现差时"毒舌"吐槽后给补救。
- 格式：使用 Markdown 列表和加粗突出重点，严禁废话。
- 输出：必须返回纯文本（Markdown），不要包裹在 ```json ... ``` 或 ```markdown ... ``` 中。
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

        try:
            reply = self.gemini.analyze_training(context)
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
        sections.append(f"\n=== 用户问题 ===\n{user_message}")

        # 组合完整提示词
        full_prompt = f"""{CHAT_SYSTEM_INSTRUCTION}

{sections}

请根据以上上下文回答用户问题。如果用户没有问具体问题，可以给出训练建议或分享有趣的洞察。
"""

        return full_prompt

    @staticmethod
    def _today() -> date:
        return date.today()
