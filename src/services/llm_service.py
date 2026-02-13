"""
LLM API Service
对接 Google Gemini，根据 Garmin 数据生成跑步教练分析。
"""
import json
from typing import Any, Dict, Union

import google.generativeai as genai

from src.core.config import settings


SYSTEM_INSTRUCTION = """
你是一个专业的跑步教练。请根据传入的 JSON 数据（包含睡眠、HRV、跑步分段数据）进行分析。
输出要求：
1. 语气专业、鼓励为主。
2. 先分析恢复状态（睡眠/静息心率）。
3. 详细点评跑步表现（如果有跑步）：关注配速稳定性、心率漂移。
4. 给出明天的训练建议。
"""


class LLMService:
    """对接 Google Gemini 的 LLM 服务。"""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model_pro = None
        self._model_flash = None

    def _get_model_pro(self):
        if self._model_pro is None:
            self._model_pro = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                system_instruction=SYSTEM_INSTRUCTION,
            )
        return self._model_pro

    def _get_model_flash(self):
        if self._model_flash is None:
            self._model_flash = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_INSTRUCTION,
            )
        return self._model_flash

    def analyze_data(self, user_data_json: Union[Dict[str, Any], str]) -> str:
        """
        根据传入的 JSON 数据生成跑步教练分析。

        - 优先使用 gemini-1.5-pro，不可用时降级为 gemini-1.5-flash。
        - 返回 AI 生成的文本内容。
        """
        if isinstance(user_data_json, dict):
            payload = json.dumps(user_data_json, ensure_ascii=False, indent=2)
        else:
            payload = str(user_data_json)

        prompt = f"请根据以下 JSON 数据进行分析：\n\n{payload}"

        for name, get_model in [("gemini-1.5-pro", self._get_model_pro), ("gemini-1.5-flash", self._get_model_flash)]:
            try:
                model = get_model()
                response = model.generate_content(prompt)
                if response and getattr(response, "text", None):
                    return response.text.strip()
            except Exception as e:
                if name == "gemini-1.5-pro":
                    continue
                raise RuntimeError(f"Gemini 请求失败（已尝试 pro 与 flash）: {e}") from e

        raise RuntimeError("Gemini 请求失败：无法获取有效回复。")
