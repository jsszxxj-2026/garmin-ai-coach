"""
Gemini Service
封装 Google Gemini API，作为项目的"大脑"，提供专业的跑步教练分析。
"""
import json
import logging
import os
import re
import time
from typing import Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from src.core.config import settings

# 初始化 logger
logger = logging.getLogger(__name__)


COACH_SYSTEM_INSTRUCTION = """
你是一名前 Garmin 首席运动科学家和专业跑步教练，但你的风格非常活泼、专业且具有真人的温情。

**人设要求**：
1. **开场白**：必须称呼用户为"冠军"、"同学"或"跑友"（随机选择，但每次都要有称呼）。
2. **语言风格**：
   - 使用大量 Emoji：🏃‍♂️（跑步）、🔥（表现好/能量）、🔋（Body Battery）、⚡（速度/爆发力）、😴（睡眠）、💪（力量）、🎯（目标）、⚠️（警告）、💥（问题）、✨（闪光点）
   - 说话要有张力：
     * 表现好时，请毫不吝啬地夸奖，用"太强了"、"这数据绝了"、"你就是我的神"等表达。
     * 表现差或身体状态不好时，要"毒舌"地吐槽（比如"你这是要累死自己吗？"、"电量都见底了还跑间歇？"），然后立即给出补救方法。
   - 严禁废话，用 Markdown 列表呈现核心发现，每条建议都要具体。

3. **分析逻辑（按优先级）**：
   - **身体电量 (Body Battery) 是最高红线**：
     * 如果 Body Battery < 40 时还跑间歇或高强度训练，你要表现出"愤怒"和"担心"（比如"🔋 电量都掉到 XX 了，你还敢跑间歇？这是要自残吗？"），然后强制建议恢复。
     * Body Battery < 30 时，必须叫停所有训练，建议休息。
   - **挖掘闪光点**：
     * 关注触地时间 (GCT/Ground Contact Time)：如果 GCT < 190ms，请狂吹彩虹屁（"✨ 触地时间 XX ms！这跑姿太完美了！你就是效率之王！"）。
     * 关注垂直比 (Vertical Ratio)：如果垂直比优秀，也要大力表扬。
   - **跑步表现分析**：
     * 关注后半程是否掉速：对比前几公里和后几公里的配速，掉速明显要"毒舌"指出。
     * 关注心率漂移：如果后半程心率明显上升但配速下降，说明疲劳累积，要指出问题。
     * 关注步频步幅变化：步频下降或步幅缩小通常表示疲劳。
   - **结合未来计划**：
     * 如果明天有大课（间歇、节奏跑等），今天必须建议恢复或轻松跑。
     * 如果明天是休息日，今天可以适当安排训练。

**输出要求**：
- 语气：活泼、专业、有张力、有温情。表现好时狂夸，表现差时"毒舌"吐槽后给补救。
- 格式：使用 Markdown 列表和加粗突出重点，严禁废话。
- 结构：
  - **开场**：用"冠军"、"同学"或"跑友"称呼用户，加 Emoji
  - **身体状态评估**：用一句话总结（良好/需注意/预警），Body Battery 低时要"愤怒"和"担心"
  - **跑步表现分析**：如果有跑步，指出关键问题或闪光点（GCT < 190ms 要狂吹彩虹屁）
  - **训练建议**：给出明天的具体建议，必须具体到时间（比如"今晚 22:00 必须关灯睡觉"、"明天早上 6:00 轻松跑 30 分钟"）
- 输出：必须返回纯文本（Markdown），不要包裹在 ```json ... ``` 或 ```markdown ... ``` 中，方便前端直接渲染。
"""


class GeminiService:
    """
    封装 Google Gemini API，提供专业的跑步教练分析。
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化 Gemini 服务。

        Args:
            model_name: 模型名称（可选，默认使用 settings.GEMINI_MODEL_NAME）
        """
        # 配置代理（如果设置了 PROXY_URL）
        if settings.PROXY_URL:
            proxy_url = settings.PROXY_URL
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url
            logger.info(f"[Gemini] 已配置代理: {proxy_url}")
        else:
            # 清除可能存在的代理设置
            os.environ.pop('http_proxy', None)
            os.environ.pop('https_proxy', None)
        
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # 可用模型诊断：仅在调试模式启用（避免每次请求都做网络调用）
        if settings.GEMINI_LIST_MODELS:
            try:
                logger.info("[Gemini] 正在查询可用模型列表...")
                available_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        model_name_found = m.name.replace('models/', '')  # 移除 'models/' 前缀
                        available_models.append(model_name_found)
                        logger.info(f"[Gemini] 发现可用模型: {model_name_found}")

                if available_models:
                    logger.info(f"[Gemini] 共找到 {len(available_models)} 个可用模型")
                else:
                    logger.warning("[Gemini] 未找到任何支持 generateContent 的模型")
            except Exception as e:
                logger.error(f"[Gemini] 无法列出模型 (可能是网络或Key问题): {e}")

        # 默认使用 settings.GEMINI_MODEL_NAME（允许通过参数覆盖）
        self.model_name = model_name or settings.GEMINI_MODEL_NAME
        self._model = None
        self._current_model_name = self.model_name
        
        logger.info(f"[Gemini] 使用模型: {self.model_name}")

    def _get_model(self):
        """
        懒加载模型实例。
        
        注意：预览版模型不支持 system_instruction 参数，因此不传入该参数。
        """
        if self._model is None:
            try:
                # 移除 system_instruction 参数，以兼容预览版模型
                self._model = genai.GenerativeModel(
                    model_name=self.model_name
                )
                logger.info(f"[Gemini] 模型实例已创建: {self.model_name}")
            except Exception as e:
                logger.warning(f"[Gemini] 模型 {self.model_name} 初始化失败: {str(e)}")
                raise
        
        return self._model

    @staticmethod
    def _parse_json_payload(text: str) -> Optional[dict]:
        raw = (text or "").strip()
        if not raw:
            return None

        # 1) direct JSON
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        # 2) fenced code block ```json ... ```
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1).strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass

        # 3) first {...} object
        first = raw.find("{")
        last = raw.rfind("}")
        if first != -1 and last > first:
            candidate = raw[first:last + 1]
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except Exception:
                return None
        return None

    def analyze_training(self, daily_report_md: str) -> str:
        """
        分析训练数据，返回 AI 教练建议。

        Args:
            daily_report_md: 由 DataProcessor 生成的 Markdown 格式日报
                           （包含跑步表现、身体状态、未来计划）

        Returns:
            AI 生成的分析建议文本（Markdown 格式）
        """
        if not daily_report_md or not daily_report_md.strip():
            logger.warning("[Gemini] 收到空数据，无法进行分析")
            return "## 📊 分析结果\n\n暂无数据，无法进行分析。"

        logger.info("[Gemini] 开始请求 Google AI 模型...")

        # 手动拼接系统指令，以兼容 Preview 模型（不支持 system_instruction 参数）
        full_prompt = f"""{COACH_SYSTEM_INSTRUCTION}

=== 用户今日数据 ===

{daily_report_md}

请按照以下结构输出：
- **身体状态评估**
- **跑步表现分析**（如果有跑步数据）
- **训练建议**
"""

        # 尝试调用 API，带重试机制
        max_retries = 2
        last_error = None
        model_name = self.model_name

        for attempt in range(max_retries):
            try:
                model = self._get_model()
                # 设置超时时间为 30 秒
                response = model.generate_content(
                    full_prompt,
                    request_options={'timeout': 30}
                )

                # 更健壮的响应处理：尝试多种方式获取文本
                result_text = None
                
                # 方法1: 尝试使用 response.text（如果可用）
                try:
                    if response and hasattr(response, "text"):
                        result_text = response.text.strip()
                except Exception as e:
                    logger.warning(f"[Gemini] 无法使用 response.text: {str(e)}")
                
                # 方法2: 如果方法1失败，尝试从 candidates 中提取
                if not result_text and response and hasattr(response, "candidates"):
                    try:
                        if response.candidates and len(response.candidates) > 0:
                            candidate = response.candidates[0]
                            if hasattr(candidate, "content") and candidate.content:
                                if hasattr(candidate.content, "parts") and candidate.content.parts:
                                    parts_text = []
                                    for part in candidate.content.parts:
                                        if hasattr(part, "text") and part.text:
                                            parts_text.append(part.text)
                                    if parts_text:
                                        result_text = "\n".join(parts_text).strip()
                    except Exception as e:
                        logger.warning(f"[Gemini] 无法从 candidates 提取文本: {str(e)}")
                
                if result_text:
                    # 清理可能的代码块标记
                    if result_text.startswith("```"):
                        # 移除开头的 ```markdown 或 ```json 等
                        lines = result_text.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        result_text = "\n".join(lines).strip()
                    logger.info(f"[Gemini] AI 响应生成完毕 (使用模型: {model_name})")
                    return result_text
                else:
                    # 如果没有获取到文本，记录详细信息
                    logger.error(f"[Gemini] 响应中没有有效的文本内容")
                    if response and hasattr(response, "candidates"):
                        for i, candidate in enumerate(response.candidates):
                            logger.error(f"[Gemini] Candidate {i}: finish_reason={getattr(candidate, 'finish_reason', 'N/A')}")
                    raise ValueError("响应中没有有效的文本内容")
                
            except google_exceptions.DeadlineExceeded as e:
                last_error = e
                logger.error(f"[Gemini] 请求超时 (模型: {model_name}, 尝试 {attempt + 1}/{max_retries}): 30秒内未收到响应")
                logger.error(f"[Gemini] 提示: 请检查网络连接或代理设置 (PROXY_URL={settings.PROXY_URL or '未设置'})")
                # 如果是第一次尝试失败，等待一下再重试
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
            except google_exceptions.ServiceUnavailable as e:
                last_error = e
                logger.error(f"[Gemini] 服务不可用 (模型: {model_name}, 尝试 {attempt + 1}/{max_retries}): {str(e)}")
                logger.error(f"[Gemini] 提示: Google API 服务暂时不可用，请稍后重试或检查代理设置")
                # 如果是第一次尝试失败，等待一下再重试
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
            except Exception as e:
                last_error = e
                logger.error(f"[Gemini] Error (模型: {model_name}, 尝试 {attempt + 1}/{max_retries}): {str(e)}")
                # 如果是第一次尝试失败，等待一下再重试
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue

        # 所有尝试都失败，返回友好的兜底回复
        error_msg = str(last_error) if last_error else "未知错误"
        logger.error(f"[Gemini] 所有重试均失败: {error_msg}")
        
        # 根据错误类型提供更具体的建议
        if isinstance(last_error, google_exceptions.DeadlineExceeded):
            suggestion = "请求超时，可能是网络连接问题。如果在中国大陆，请检查是否配置了代理 (PROXY_URL)。"
        elif isinstance(last_error, google_exceptions.ServiceUnavailable):
            suggestion = "Google API 服务暂时不可用，请稍后重试。"
        else:
            suggestion = "请检查网络连接、代理设置或稍后重试。"
        
        return f"""## 📊 分析结果

教练正在看表，稍后再试...

**错误信息**: {error_msg}

**建议**: {suggestion}
"""

    def analyze_training_with_fallback(self, daily_report_md: str) -> str:
        """
        分析训练数据，带模型降级机制。

        注意：当前强制使用 gemini-3-flash-preview，此方法仅保留接口兼容性。

        Args:
            daily_report_md: 由 DataProcessor 生成的 Markdown 格式日报

        Returns:
            AI 生成的分析建议文本（Markdown 格式）
        """
        # 直接使用当前模型（已强制为 gemini-3-flash-preview）
        return self.analyze_training(daily_report_md)

    def generate_home_summary_brief(
        self,
        *,
        week_stats: dict,
        month_stats: dict,
        run_count: int,
        sleep_days: int,
    ) -> dict[str, Optional[str]]:
        if run_count < 3 or sleep_days < 3:
            return {"week": None, "month": None}

        prompt_payload = {
            "run_count_30d": run_count,
            "sleep_days_30d": sleep_days,
            "week_stats": week_stats,
            "month_stats": month_stats,
        }
        prompt = (
            "你是跑步教练，请根据数据输出简短首页简评。\n"
            "仅返回 JSON：{\"week\": string|null, \"month\": string|null}。\n"
            "要求：每条不超过 40 字，不要换行，不要 Markdown。\n"
            f"输入数据: {json.dumps(prompt_payload, ensure_ascii=False)}"
        )

        try:
            result_text = self.analyze_training(prompt)
            data = self._parse_json_payload(result_text)
            if not isinstance(data, dict):
                raise ValueError("Gemini 返回非 JSON 内容")
            week = data.get("week") if isinstance(data, dict) else None
            month = data.get("month") if isinstance(data, dict) else None
            return {
                "week": str(week) if week else None,
                "month": str(month) if month else None,
            }
        except Exception as e:
            logger.warning(f"[Gemini] Home summary brief failed: {e}")
            return {"week": None, "month": None}
