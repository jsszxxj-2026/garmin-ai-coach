"""
获取近一个月的 Garmin 数据，并保存为一个 JSON 文件。

运行：./venv/bin/python3 scripts/export_monthly_data.py
 或：source venv/bin/activate && python3 scripts/export_monthly_data.py

输出：项目根目录下 garmin_monthly_YYYY-MM-DD.json（按结束日期命名）
"""
import json
import sys
import os
import time
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.services.garmin_service import GarminService


def main():
    end_date = date.today()
    start_date = end_date - timedelta(days=29)  # 共 30 天
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_file = os.path.join(project_root, f"garmin_monthly_{end_date.isoformat()}.json")

    try:
        garmin = GarminService(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
    except Exception as e:
        print(f"❌ Garmin 初始化/登录失败: {e}")
        print("💡 请检查 .env 中的 GARMIN_EMAIL、GARMIN_PASSWORD 及 GARMIN_IS_CN。")
        sys.exit(1)

    days = []
    total = (end_date - start_date).days + 1

    for i in range(total):
        d = start_date + timedelta(days=i)
        date_str = d.isoformat()
        print(f"  [{i+1}/{total}] {date_str} ...", end=" ", flush=True)
        try:
            data = garmin.get_daily_data(date_str)
            days.append(data)
            n = len(data.get("activities") or [])
            print(f"✓ 运动 {n} 条")
        except Exception as e:
            days.append({"date": date_str, "error": str(e)})
            print(f"✗ {e}")
        if i < total - 1:
            time.sleep(0.5)  # 降低请求频率，避免触发限制

    payload = {
        "exported_at": datetime.now().isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": days,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ 已保存: {out_file}")


if __name__ == "__main__":
    main()
