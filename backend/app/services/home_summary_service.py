from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.app.services.gemini_service import GeminiService
from src.core.config import settings

logger = logging.getLogger(__name__)


class HomeSummaryService:
    def __init__(self, *, gemini: Optional[GeminiService] = None) -> None:
        self.gemini = gemini or GeminiService()

    def should_generate_ai_brief(self) -> bool:
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
        if not self.should_generate_ai_brief():
            return {}
        return {}
