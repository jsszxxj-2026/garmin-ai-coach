"""
Garmin 连通性测试脚本。
运行方式（任选其一）：
  1. source venv/bin/activate && python3 scripts/test_garmin_auth.py
  2. ./venv/bin/python3 scripts/test_garmin_auth.py
"""
import sys
import os

# 将项目根目录加入 python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from garminconnect import Garmin
from src.core.config import settings
from datetime import date

def test_connection():
    domain = "connect.garmin.cn（中国）" if settings.GARMIN_IS_CN else "connect.garmin.com（国际）"
    print(f"🔐 正在尝试登录 Garmin 账号: {settings.GARMIN_EMAIL} （{domain}）...")
    
    try:
        # 初始化 Garmin 客户端（is_cn=True 表示中国区 connect.garmin.cn）
        client = Garmin(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD, is_cn=settings.GARMIN_IS_CN)
        client.login()
        print("✅ 登录成功！")
        
        # 获取显示名称
        full_name = client.full_name
        print(f"👋 你好, {full_name}!")
        
        # 尝试获取今日摘要
        today = date.today().isoformat()
        stats = client.get_user_summary(today)
        
        print(f"\n📅 今日 ({today}) 数据预览:")
        if 'totalSteps' in stats:
            print(f"- 步数: {stats['totalSteps']}")
        if 'restingHeartRate' in stats:
            print(f"- 静息心率: {stats['restingHeartRate']}")
            
        print("\n🚀 环境配置完美！Garmin 连接正常。")
        
    except Exception as e:
        err = str(e)
        print(f"\n❌ 连接失败: {err}")
        print("💡 排查建议：")
        print("  1. 账号/密码：确认 .env 中 GARMIN_EMAIL、GARMIN_PASSWORD 正确，且能在浏览器登录对应站点。")
        if "401" in err or "Unauthorized" in err:
            print("  2. 中国区/国际区：若你用的是 Garmin 中国 (connect.garmin.cn)，在 .env 中增加：GARMIN_IS_CN=true")
        print("  3. 密码中如有特殊字符，可先改成纯字母数字测试。")
        print("  4. 网络：若所在地区或网络受限，可尝试换网络或 VPN。")

if __name__ == "__main__":
    test_connection()
