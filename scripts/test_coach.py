"""
串联 Garmin 与 AI 教练的测试脚本。
- 初始化 GarminService、LLMService
- 获取今天的数据
- 调用 AI 分析并打印结果

运行：./venv/bin/python3 scripts/test_coach.py
 或：source venv/bin/activate && python3 scripts/test_coach.py
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.services.garmin_service import GarminService
from src.services.llm_service import LLMService


def main():
    today = date.today().isoformat()

    # 1. 初始化服务
    try:
        garmin = GarminService(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
    except Exception as e:
        print(f"❌ Garmin 初始化/登录失败: {e}")
        print("💡 请检查 .env 中的 GARMIN_EMAIL、GARMIN_PASSWORD 及 GARMIN_IS_CN。")
        sys.exit(1)

    try:
        llm = LLMService()
    except Exception as e:
        print(f"❌ LLM 初始化失败: {e}")
        print("💡 请检查 .env 中的 GEMINI_API_KEY。")
        sys.exit(1)

    # 2. 获取今日数据
    try:
        data = garmin.get_daily_data(today)
    except Exception as e:
        print(f"❌ 获取 Garmin 数据失败: {e}")
        sys.exit(1)

    # 简单判断是否有可分析内容
    has_content = (
        data.get("sleep_score") is not None
        or data.get("resting_heart_rate") is not None
        or (data.get("activities") or [])
    )
    if not has_content:
        print(f"📭 {today} 暂无睡眠、静息心率或运动数据，无法进行分析。")
        print("   请稍后再试或更换日期。")
        sys.exit(0)

    print(f"📅 已获取 {today} 数据：睡眠分数={data.get('sleep_score')}，静息心率={data.get('resting_heart_rate')}，运动数={len(data.get('activities') or [])}")

    # 3. AI 分析
    print("\n🤔 正在思考...")
    try:
        result = llm.analyze_data(data)
    except Exception as e:
        print(f"❌ AI 分析请求失败: {e}")
        print("💡 请检查 GEMINI_API_KEY 是否有效、网络是否正常。")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("📋 教练分析")
    print("=" * 60)
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    main()
