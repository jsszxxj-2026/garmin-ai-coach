"""
清洗指定日期的 Garmin 数据。

用法: python3 scripts/clean_dates.py 2026-01-23 2026-01-24
 或: python3 scripts/clean_dates.py 2026-01-23  # 只清洗一天
"""
import json
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.data_processor import DataProcessor
from backend.app.services.garmin_client import GarminClient
from src.services.garmin_service import GarminService
from src.core.config import settings


def clean_date(date_str: str, processor: DataProcessor, output_dir: str = "."):
    """清洗单日数据并保存。"""
    print(f"\n{'='*60}")
    print(f"📅 处理日期: {date_str}")
    print(f"{'='*60}")

    yesterday = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    results = {}

    # 1. 活动数据（昨天的活动）
    print(f"\n1️⃣ 获取 {yesterday} 的活动数据...")
    try:
        garmin_service = GarminService(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
        daily_data = garmin_service.get_daily_data(yesterday)
        activities = daily_data.get("activities") or []

        if activities:
            simplified = [processor.simplify_activity(a) for a in activities]
            activity_md = processor.format_for_llm(simplified)
            results["activity"] = activity_md
            print(f"✅ 找到 {len(activities)} 个活动")
        else:
            print(f"⚠️  无活动数据")
            results["activity"] = None
    except Exception as e:
        print(f"❌ 失败: {e}")
        results["activity"] = None

    # 2. 健康数据（今天的健康状态）
    print(f"\n2️⃣ 获取 {date_str} 的健康数据...")
    try:
        client = GarminClient()
        health_data = client.get_health_stats(date_str)

        if health_data:
            health_md = processor.format_health_summary(health_data)
            results["health"] = health_md
            print("✅ 健康数据获取成功")
        else:
            print("⚠️  无健康数据")
            results["health"] = None
    except Exception as e:
        print(f"❌ 失败: {e}")
        results["health"] = None

    # 3. 训练计划
    print(f"\n3️⃣ 获取未来训练计划...")
    try:
        client = GarminClient()
        plan_data = client.get_training_plan(date_str, days=3)

        if plan_data:
            plan_md = processor.format_future_plan(plan_data)
            results["plan"] = plan_md
            print(f"✅ 找到 {len(plan_data)} 个计划")
        else:
            print("⚠️  无训练计划")
            results["plan"] = None
    except Exception as e:
        print(f"❌ 失败: {e}")
        results["plan"] = None

    # 4. 组合完整日报
    print(f"\n4️⃣ 生成完整日报...")
    full_report = processor.assemble_daily_report(
        results.get("activity"),
        results.get("health"),
        results.get("plan"),
    )

    # 保存文件
    files_saved = []
    if results.get("activity"):
        fname = os.path.join(output_dir, f"cleaned_activities_{yesterday}.md")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(results["activity"])
        files_saved.append(fname)

    if results.get("health"):
        fname = os.path.join(output_dir, f"cleaned_health_{date_str}.md")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(results["health"])
        files_saved.append(fname)

    if results.get("plan"):
        fname = os.path.join(output_dir, f"cleaned_plan_{date_str}.md")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(results["plan"])
        files_saved.append(fname)

    if full_report:
        fname = os.path.join(output_dir, f"daily_report_{date_str}.md")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(full_report)
        files_saved.append(fname)

    print(f"\n💾 已保存 {len(files_saved)} 个文件:")
    for f in files_saved:
        print(f"   - {f}")

    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/clean_dates.py YYYY-MM-DD [YYYY-MM-DD ...]")
        print("示例: python3 scripts/clean_dates.py 2026-01-23 2026-01-24")
        sys.exit(1)

    dates = sys.argv[1:]
    processor = DataProcessor()

    print(f"🚀 开始清洗 {len(dates)} 天的数据...")

    for date_str in dates:
        try:
            # 验证日期格式
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"❌ 无效日期格式: {date_str}，应为 YYYY-MM-DD")
            continue

        try:
            clean_date(date_str, processor)
        except Exception as e:
            print(f"❌ 处理 {date_str} 时出错: {e}")
            continue

    print(f"\n{'='*60}")
    print("✅ 所有日期处理完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
