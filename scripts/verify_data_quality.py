# scripts/verify_data_quality.py
import sys
import os
import json
from datetime import date

# 确保能导入 src 目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.services.garmin_service import GarminService

def verify():
    print("🕵️‍♂️ 正在启动数据质量检查...")
    
    # 1. 登录
    try:
        service = GarminService(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return

    # 2. 获取数据 (默认今天，如果没有数据，请手动修改为昨天，例如 "2024-05-20")
    #target_date = date.today().isoformat() 
    target_date = "2026-01-23" # <--- 如果今天没跑，把这行注释打开并填入你有跑步记录的日期
    
    print(f"📥 正在抓取并清洗 {target_date} 的数据...")
    try:
        clean_data = service.get_daily_data(target_date)
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. 保存到文件 (方便肉眼检查)
    filename = f"cleaned_data_{target_date}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ 数据已保存到: {filename}")
    print("-" * 30)
    
    # 4. 关键指标检查 (自动判断数据够不够“豪华”)
    print("🧐 正在进行‘体检’...")
    
    # 检查睡眠
    sleep = clean_data.get('summary', {}).get('sleep', {})
    if 'deep' in sleep and 'rem' in sleep:
        print(f"✅ [睡眠] 深层/REM数据已提取: 深睡 {sleep['deep']}, REM {sleep['rem']}")
    else:
        print("⚠️ [睡眠] 警告: 缺少深睡/REM数据，只有总时长")

    # 检查运动
    activities = clean_data.get('activities', [])
    if not activities:
        print("⚠️ [运动] 当日无运动记录，无法检查跑步详情。")
    else:
        for act in activities:
            if act['type'] == 'Running':
                print(f"🏃 发现跑步活动: {act['name']}")
                
                # 检查分段
                laps = act.get('laps', [])
                if len(laps) > 1:
                    print(f"✅ [分段] 成功提取 {len(laps)} 个分段数据。")
                    print(f"   - 第1公里配速: {laps[0].get('pace')}")
                    print(f"   - 第1公里心率: {laps[0].get('hr')}")
                else:
                    print("⚠️ [分段] 警告: 没有提取到每公里的分段数据 (Splits)！")
                
                # 检查高阶指标
                metrics = act.get('metrics', {})
                if 'avg_cadence' in metrics:
                    print(f"✅ [步频] 平均步频: {metrics['avg_cadence']}")
                else:
                    print("⚠️ [步频] 缺失")
                    
                if 'avg_gct' in metrics or 'avg_vertical_ratio' in metrics:
                    print(f"✅ [高阶] 跑步动力学 (GCT/垂直比) 已提取")
                else:
                    print("ℹ️ [高阶] 未发现跑步动力学数据 (可能设备不支持或未佩戴心率带)")

if __name__ == "__main__":
    verify()