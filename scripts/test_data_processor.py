"""
测试 DataProcessor 数据清洗功能，查看清理后的数据输出。

运行：
  ./venv/bin/python3 scripts/test_data_processor.py
  ./venv/bin/python3 scripts/test_data_processor.py 2026-01-23  # 指定日期
  source venv/bin/activate && python3 scripts/test_data_processor.py
"""
import json
import sys
import os
from datetime import date, timedelta, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.data_processor import DataProcessor
from backend.app.services.garmin_client import GarminClient
from src.services.garmin_service import GarminService
from src.core.config import settings


def main():
    # 解析命令行参数：如果提供了日期，使用该日期
    target_date_str = None
    if len(sys.argv) > 1:
        target_date_str = sys.argv[1]
        try:
            # 验证日期格式
            datetime.strptime(target_date_str, "%Y-%m-%d")
        except ValueError:
            print(f"❌ 无效的日期格式: {target_date_str}")
            print("   日期格式应为: YYYY-MM-DD (例如: 2026-01-23)")
            sys.exit(1)
    
    # 确定要处理的日期
    if target_date_str:
        # 如果提供了日期，活动数据和健康数据都从该日期获取
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        activity_date = target_date.isoformat()  # 活动数据从指定日期获取
        health_date = target_date.isoformat()   # 健康数据从指定日期获取
        print(f"📅 处理指定日期: {target_date_str}")
    else:
        # 默认：活动从昨天，健康从今天
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        activity_date = yesterday  # 活动数据从昨天获取
        health_date = today         # 健康数据从今天获取
        print(f"📅 处理默认日期: 活动 {activity_date}, 健康 {health_date}")
    
    processor = DataProcessor()

    print("\n" + "=" * 60)
    print("📊 DataProcessor 数据清洗测试")
    if target_date_str:
        print(f"   目标日期: {target_date_str}")
    print("=" * 60)

    # 1. 测试活动数据清洗
    print("\n1️⃣ 测试活动数据清洗...")
    try:
        garmin_service = GarminService(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
        all_activities = []
        
        # 先查询指定日期的活动
        daily_data = garmin_service.get_daily_data(activity_date)
        activities = daily_data.get("activities") or []
        if activities:
            all_activities.extend(activities)
            print(f"✅ 从 {activity_date} 找到 {len(activities)} 个活动")
        
        # 只处理当天的数据，不再查询前一天

        if all_activities:
            # 将新格式的活动数据转换为 simplify_activity 期望的格式
            converted_activities = []
            for act in all_activities:
                # 新格式：{type, name, metrics, laps}
                # 旧格式：{distance, duration, averageHR, splits, ...}
                if "metrics" in act:
                    # 新格式，需要转换
                    metrics = act.get("metrics", {})
                    converted = {
                        "type": act.get("type"),
                        "activityName": act.get("name"),
                        "distance": metrics.get("distance_km", 0) * 1000 if metrics.get("distance_km") else None,
                        "duration": metrics.get("duration_seconds"),
                        "averageHR": metrics.get("average_hr"),
                        "maxHR": metrics.get("max_hr"),
                        "averageSpeed": None,
                        "startTimeLocal": act.get("start_time_local") or "",  # 从新格式中获取时间
                    }
                    
                    # 如果有配速，尝试反推速度
                    pace_str = metrics.get("average_pace", "")
                    if pace_str and pace_str != "N/A" and "'" in pace_str:
                        try:
                            # 解析 "5'30\"/km" 格式
                            pace_part = pace_str.split("'")[0]
                            minutes = float(pace_part)
                            speed_mps = 1000.0 / (60 * minutes)
                            converted["averageSpeed"] = speed_mps
                        except:
                            pass
                    
                    # 将 laps 转换为 splits 格式
                    laps = act.get("laps", [])
                    splits = []
                    for lap in laps:
                        split = {
                            "lapIndex": lap.get("lap_index"),
                            "distance": lap.get("distance_km", 0) * 1000 if lap.get("distance_km") else None,
                            "duration": lap.get("duration_seconds"),
                            "averageHR": lap.get("average_hr"),
                            "maxHR": lap.get("max_hr"),
                            "strideLength": lap.get("stride_length_cm"),
                            "groundContactTime": lap.get("ground_contact_time_ms"),
                            "verticalOscillation": lap.get("vertical_oscillation_cm"),
                            "verticalRatio": lap.get("vertical_ratio_percent"),
                            "averageRunCadence": lap.get("cadence"),
                        }
                        # 从配速反推速度
                        lap_pace = lap.get("pace", "")
                        if lap_pace and lap_pace != "N/A" and "'" in lap_pace:
                            try:
                                pace_part = lap_pace.split("'")[0]
                                minutes = float(pace_part)
                                speed_mps = 1000.0 / (60 * minutes)
                                split["averageSpeed"] = speed_mps
                            except:
                                pass
                        splits.append(split)
                    converted["splits"] = splits
                    converted_activities.append(converted)
                else:
                    # 已经是旧格式，直接使用
                    converted_activities.append(act)
            
            # 简化活动数据
            simplified = [processor.simplify_activity(a) for a in converted_activities]
            # 格式化为 Markdown
            activity_md = processor.format_for_llm(simplified)
            print("\n✅ 活动数据清洗完成")
            print("\n" + "-" * 60)
            print("清理后的活动数据 (Markdown):")
            print("-" * 60)
            print(activity_md)
            print("-" * 60)

            # 保存到文件
            output_file = f"cleaned_activities_{activity_date}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(activity_md)
            print(f"\n💾 已保存到: {output_file}")
        else:
            print(f"⚠️  {activity_date} 没有活动数据")
    except Exception as e:
        print(f"❌ 活动数据清洗失败: {e}")

    # 2. 测试健康数据清洗
    print("\n2️⃣ 测试健康数据清洗...")
    try:
        client = GarminClient()
        health_data = client.get_health_stats(health_date)

        if health_data:
            health_md = processor.format_health_summary(health_data)
            print("\n✅ 健康数据清洗完成")
            print("\n" + "-" * 60)
            print("清理后的健康数据 (Markdown):")
            print("-" * 60)
            print(health_md)
            print("-" * 60)

            # 保存到文件
            output_file = f"cleaned_health_{health_date}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(health_md)
            print(f"\n💾 已保存到: {output_file}")
        else:
            print(f"⚠️  {health_date} 没有健康数据")
    except Exception as e:
        print(f"❌ 健康数据清洗失败: {e}")

    # 3. 测试训练计划清洗
    print("\n3️⃣ 测试训练计划清洗...")
    try:
        client = GarminClient()
        plan_data = client.get_training_plan(health_date, days=3)

        if plan_data:
            plan_md = processor.format_future_plan(plan_data)
            print("\n✅ 训练计划清洗完成")
            print("\n" + "-" * 60)
            print("清理后的训练计划 (Markdown):")
            print("-" * 60)
            print(plan_md)
            print("-" * 60)

            # 保存到文件
            output_file = f"cleaned_plan_{health_date}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(plan_md)
            print(f"\n💾 已保存到: {output_file}")
        else:
            print(f"⚠️  未来3天没有训练计划")
    except Exception as e:
        print(f"❌ 训练计划清洗失败: {e}")

    # 4. 测试完整日报组合
    print("\n4️⃣ 测试完整日报组合...")
    try:
        # 重新获取数据（如果之前失败）
        if "activity_md" not in locals():
            garmin_service = GarminService(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
            all_activities = []
            
            # 先查询指定日期的活动
            daily_data = garmin_service.get_daily_data(activity_date)
            activities = daily_data.get("activities") or []
            if activities:
                all_activities.extend(activities)
            
            # 只处理当天的数据，不再查询前一天
            
            if all_activities:
                # 将新格式的活动数据转换为 simplify_activity 期望的格式
                converted_activities = []
                for act in all_activities:
                    if "metrics" in act:
                        # 新格式，需要转换
                        metrics = act.get("metrics", {})
                        converted = {
                            "type": act.get("type"),
                            "activityName": act.get("name"),
                            "distance": metrics.get("distance_km", 0) * 1000 if metrics.get("distance_km") else None,
                            "duration": metrics.get("duration_seconds"),
                            "averageHR": metrics.get("average_hr"),
                            "maxHR": metrics.get("max_hr"),
                            "averageSpeed": None,
                            "startTimeLocal": act.get("start_time_local") or "",  # 保留运动时间
                        }
                        
                        # 如果有配速，尝试反推速度
                        pace_str = metrics.get("average_pace", "")
                        if pace_str and pace_str != "N/A" and "'" in pace_str:
                            try:
                                pace_part = pace_str.split("'")[0]
                                minutes = float(pace_part)
                                speed_mps = 1000.0 / (60 * minutes)
                                converted["averageSpeed"] = speed_mps
                            except:
                                pass
                        
                        # 将 laps 转换为 splits 格式
                        laps = act.get("laps", [])
                        splits = []
                        for lap in laps:
                            split = {
                                "lapIndex": lap.get("lap_index"),
                                "distance": lap.get("distance_km", 0) * 1000 if lap.get("distance_km") else None,
                                "duration": lap.get("duration_seconds"),
                                "averageHR": lap.get("average_hr"),
                                "maxHR": lap.get("max_hr"),
                                "strideLength": lap.get("stride_length_cm"),
                                "groundContactTime": lap.get("ground_contact_time_ms"),
                                "verticalOscillation": lap.get("vertical_oscillation_cm"),
                                "verticalRatio": lap.get("vertical_ratio_percent"),
                                "averageRunCadence": lap.get("cadence"),
                            }
                            # 从配速反推速度
                            lap_pace = lap.get("pace", "")
                            if lap_pace and lap_pace != "N/A" and "'" in lap_pace:
                                try:
                                    pace_part = lap_pace.split("'")[0]
                                    minutes = float(pace_part)
                                    speed_mps = 1000.0 / (60 * minutes)
                                    split["averageSpeed"] = speed_mps
                                except:
                                    pass
                            splits.append(split)
                        converted["splits"] = splits
                        converted_activities.append(converted)
                    else:
                        converted_activities.append(act)
                
                simplified = [processor.simplify_activity(a) for a in converted_activities]
                activity_md = processor.format_for_llm(simplified)
            else:
                activity_md = None

        if "health_md" not in locals():
            client = GarminClient()
            health_data = client.get_health_stats(health_date)
            health_md = processor.format_health_summary(health_data) if health_data else None

        if "plan_md" not in locals():
            client = GarminClient()
            plan_data = client.get_training_plan(health_date, days=3)
            plan_md = processor.format_future_plan(plan_data) if plan_data else None

        full_report = processor.assemble_daily_report(activity_md, health_md, plan_md, activity_date=activity_date)
        print("\n✅ 完整日报组合完成")
        print("\n" + "=" * 60)
        print("完整日报 (Markdown):")
        print("=" * 60)
        print(full_report)
        print("=" * 60)

        # 保存到文件
        output_file = f"daily_report_{health_date}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_report)
        print(f"\n💾 已保存到: {output_file}")
    except Exception as e:
        print(f"❌ 完整日报组合失败: {e}")

    print("\n" + "=" * 60)
    print("✅ 测试完成！清理后的数据已保存到当前目录的 .md 文件中")
    print("=" * 60)


if __name__ == "__main__":
    main()
