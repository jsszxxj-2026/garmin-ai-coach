"""
LLM Factory
根据配置动态选择 LLM 服务（DeepSeek、SiliconFlow 或 Gemini）。
"""

from __future__ import annotations

import logging
from typing import Optional, Union

from src.core.config import settings

logger = logging.getLogger(__name__)

# 类型别名：LLM 服务实例（DeepSeekService、SiliconFlowService 或 GeminiService，接口一致）
LLMService = Union["DeepSeekService", "SiliconFlowService", "GeminiService"]  # noqa: F821


def get_llm_service(model_name: Optional[str] = None) -> LLMService:
    """
    根据 settings.LLM_PROVIDER 返回对应的 LLM 服务实例。

    Args:
        model_name: 可选的模型名覆盖

    Returns:
        DeepSeekService、SiliconFlowService 或 GeminiService 实例（接口一致）

    Raises:
        ValueError: 如果 LLM_PROVIDER 不支持
    """
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "deepseek":
        from backend.app.services.deepseek_service import DeepSeekService

        logger.info("[LLM Factory] 使用 DeepSeek 服务")
        return DeepSeekService(model_name=model_name)

    elif provider == "siliconflow":
        from backend.app.services.siliconflow_service import SiliconFlowService

        logger.info("[LLM Factory] 使用 SiliconFlow (硅基流动) 服务")
        return SiliconFlowService(model_name=model_name)

    elif provider == "gemini":
        from backend.app.services.gemini_service import GeminiService

        logger.info("[LLM Factory] 使用 Gemini 服务")
        return GeminiService(model_name=model_name)

    else:
        raise ValueError(
            f"不支持的 LLM_PROVIDER: '{provider}'，"
            "请在 .env 中设置为 'deepseek'、'siliconflow' 或 'gemini'"
        )
