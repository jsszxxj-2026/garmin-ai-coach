"""
Application Configuration
"""
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GARMIN_EMAIL: str
    GARMIN_PASSWORD: str
    GEMINI_API_KEY: str
    GARMIN_IS_CN: bool = False  # True = connect.garmin.cn（中国），False = connect.garmin.com（国际）
    PROXY_URL: Optional[str] = None  # 代理 URL，用于访问 Google API（例如：http://127.0.0.1:7890）

    # Database
    DATABASE_URL: Optional[str] = None  # e.g. mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4

    # Gemini
    GEMINI_LIST_MODELS: bool = False  # 调试用：启动时列出可用模型
    GEMINI_MODEL_NAME: str = "gemini-3-flash-preview"

    # Runtime behavior
    USE_MOCK_MODE: bool = False
    ANALYSIS_CACHE_HOURS: int = 24
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略多余的配置项


settings = Settings()
