#!/usr/bin/env python3
"""
数据库迁移脚本：创建新表 user_profiles 和 chat_messages

使用方法:
    python3 scripts/migrate_create_tables.py

说明:
    此脚本会在数据库中创建新表（如果不存在）。
    依赖于 backend/app/db/models.py 中定义的 SQLAlchemy 模型。
"""
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.db.base import Base
from backend.app.db.models import UserProfile, ChatMessage
from backend.app.db.session import get_engine
from src.core.config import settings


def migrate():
    """创建新表"""
    if not settings.DATABASE_URL:
        print("错误: DATABASE_URL 未设置")
        sys.exit(1)

    print(f"[Migration] 连接数据库: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")

    engine = get_engine()

    # 创建新表
    print("[Migration] 正在创建表...")
    
    # 创建 user_profiles 表
    UserProfile.__table__.create(bind=engine, checkfirst=True)
    print("  - user_profiles: OK")

    # 创建 chat_messages 表
    ChatMessage.__table__.create(bind=engine, checkfirst=True)
    print("  - chat_messages: OK")

    print("[Migration] 完成!")


if __name__ == "__main__":
    migrate()
