"""
GarminCoach - FastAPI Application
提供 RESTful API 接口，整合 Garmin 数据和 AI 教练分析。
"""
import logging
import sys
import os
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置全局 Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ProjectRunner")

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy.orm import Session

from backend.app.api.wechat import router as wechat_router
from backend.app.services.garmin_client import GarminClient
from backend.app.services.data_processor import DataProcessor
from backend.app.services.gemini_service import GeminiService
from backend.app.services.home_summary_service import HomeSummaryService
from backend.app.services.report_service import ReportService
from backend.app.jobs.scheduler import start_scheduler
from backend.app.db.crud import get_home_summary, upsert_home_summary
from backend.app.db.models import WechatUser
from backend.app.db.session import get_db_optional, init_db
from src.services.garmin_service import GarminService
from src.core.config import settings


# 初始化 FastAPI 应用
app = FastAPI(
    title="GarminCoach API",
    description="基于 Garmin 数据和 AI 的跑步教练分析服务",
    version="1.0.0",
)

app.include_router(wechat_router)

_scheduler = None


@app.on_event("startup")
def _startup() -> None:
    try:
        init_db()
    except Exception as e:
        logger.error(f"[DB] Startup init failed: {e}")

    global _scheduler
    if settings.ENABLE_GARMIN_POLLING:
        try:
            _scheduler = start_scheduler()
        except Exception as e:
            logger.error(f"[Scheduler] Startup failed: {e}")


@app.on_event("shutdown")
def _shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"[Scheduler] Shutdown failed: {e}")
        finally:
            _scheduler = None

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请配置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 响应模型
class DailyAnalysisResponse(BaseModel):
    """每日分析响应模型"""
    date: str
    raw_data_summary: str  # 清洗后的 Markdown 文本，用于前端展示数据概览
    ai_advice: str  # Gemini 的建议
    charts: Optional[Dict[str, List]] = None  # 图表数据（labels, paces, heart_rates, cadences）


class HomeSummaryResponse(BaseModel):
    latest_run: Optional[Dict[str, Any]] = None
    week_stats: Optional[Dict[str, Any]] = None
    month_stats: Optional[Dict[str, Any]] = None
    ai_brief: Optional[Dict[str, Any]] = None
    updated_at: Optional[str] = None


class PeriodAnalysisResponse(BaseModel):
    period: str  # "week" or "month"
    start_date: str
    end_date: str
    run_count: int
    total_distance_km: float
    avg_speed_kmh: Optional[float] = None
    sleep_days: int
    avg_sleep_hours: Optional[float] = None
    ai_analysis: Optional[str] = None


# Mock Mode 开关（通过 .env 配置）
USE_MOCK_MODE = settings.USE_MOCK_MODE

# 依赖注入：初始化服务实例
def get_garmin_client() -> Optional[GarminClient]:
    """
    获取 GarminClient 实例（依赖注入）。
    
    注意：每次请求都会创建新实例并登录，如果频繁调用可能触发 Garmin 限流。
    生产环境建议使用连接池或缓存机制。
    
    Mock Mode: 如果 USE_MOCK_MODE=True，返回 None（不需要真实的客户端）。
    """
    if USE_MOCK_MODE:
        # Mock Mode: 不需要真实的客户端，返回 None
        return None
    else:
        try:
            return GarminClient()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Garmin 登录失败: {str(e)}。请检查 .env 文件中的账号密码是否正确。"
            )


def get_garmin_service() -> Optional[GarminService]:
    """
    获取 GarminService 实例（依赖注入）。
    
    用于获取活动数据。
    
    Mock Mode: 如果 USE_MOCK_MODE=True，返回 None（不需要真实服务）。
    """
    if USE_MOCK_MODE:
        return None
    else:
        try:
            return GarminService(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Garmin 服务初始化失败: {str(e)}"
            )


def get_data_processor() -> DataProcessor:
    """获取 DataProcessor 实例（依赖注入）。"""
    return DataProcessor()


def get_gemini_service() -> GeminiService:
    """获取 GeminiService 实例（依赖注入）。"""
    global _gemini_singleton
    if _gemini_singleton is None:
        _gemini_singleton = GeminiService()
    return _gemini_singleton


def get_report_service(
    processor: DataProcessor = Depends(get_data_processor),
    gemini: GeminiService = Depends(get_gemini_service),
) -> ReportService:
    return ReportService(processor=processor, gemini=gemini)


def get_home_summary_service(
    gemini: GeminiService = Depends(get_gemini_service),
) -> HomeSummaryService:
    return HomeSummaryService(gemini=gemini)


_gemini_singleton: Optional[GeminiService] = None


def _convert_activity_for_processor(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Convert the new parsed activity format into DataProcessor's expected format."""

    if not isinstance(activity, dict) or "metrics" not in activity:
        return activity

    metrics = activity.get("metrics") if isinstance(activity.get("metrics"), dict) else {}
    distance_km = metrics.get("distance_km")
    duration_s = metrics.get("duration_seconds")
    distance_m = float(distance_km) * 1000.0 if isinstance(distance_km, (int, float)) else None

    avg_speed_mps = None
    if isinstance(distance_m, (int, float)) and isinstance(duration_s, (int, float)) and float(duration_s) > 0:
        avg_speed_mps = float(distance_m) / float(duration_s)

    converted: Dict[str, Any] = {
        "type": activity.get("type"),
        "activityName": activity.get("name"),
        "distance": distance_m,
        "duration": duration_s,
        "averageHR": metrics.get("average_hr"),
        "maxHR": metrics.get("max_hr"),
        "averageSpeed": avg_speed_mps,
        "startTimeLocal": activity.get("start_time_local") or activity.get("startTimeLocal") or "",
    }

    laps = activity.get("laps") if isinstance(activity.get("laps"), list) else []
    splits: List[Dict[str, Any]] = []
    for lap in laps:
        if not isinstance(lap, dict):
            continue
        lap_distance_km = lap.get("distance_km")
        lap_duration_s = lap.get("duration_seconds")
        lap_distance_m = float(lap_distance_km) * 1000.0 if isinstance(lap_distance_km, (int, float)) else None

        lap_speed_mps = None
        if (
            isinstance(lap_distance_m, (int, float))
            and isinstance(lap_duration_s, (int, float))
            and float(lap_duration_s) > 0
        ):
            lap_speed_mps = float(lap_distance_m) / float(lap_duration_s)

        splits.append(
            {
                "lapIndex": lap.get("lap_index"),
                "distance": lap_distance_m,
                "duration": lap_duration_s,
                "averageHR": lap.get("average_hr"),
                "maxHR": lap.get("max_hr"),
                "strideLength": lap.get("stride_length_cm"),
                "groundContactTime": lap.get("ground_contact_time_ms"),
                "verticalOscillation": lap.get("vertical_oscillation_cm"),
                "verticalRatio": lap.get("vertical_ratio_percent"),
                "averageRunCadence": lap.get("cadence"),
                "averageSpeed": lap_speed_mps,
            }
        )

    converted["splits"] = splits
    return converted


def _activity_to_new_format_from_db(activity: Any) -> Dict[str, Any]:
    metrics = {
        "distance_km": activity.distance_km,
        "duration_seconds": activity.duration_seconds,
        "average_hr": activity.average_hr,
        "max_hr": activity.max_hr,
        "calories": activity.calories,
        "average_cadence": activity.average_cadence,
        "average_stride_length_cm": activity.average_stride_length_cm,
        "average_ground_contact_time_ms": activity.average_ground_contact_time_ms,
        "average_vertical_oscillation_cm": activity.average_vertical_oscillation_cm,
        "average_vertical_ratio_percent": activity.average_vertical_ratio_percent,
    }
    laps = []
    for lap in activity.laps or []:
        laps.append(
            {
                "lap_index": lap.lap_index,
                "distance_km": lap.distance_km,
                "duration_seconds": lap.duration_seconds,
                "average_hr": lap.average_hr,
                "max_hr": lap.max_hr,
                "cadence": lap.cadence,
                "stride_length_cm": lap.stride_length_cm,
                "ground_contact_time_ms": lap.ground_contact_time_ms,
                "vertical_oscillation_cm": lap.vertical_oscillation_cm,
                "vertical_ratio_percent": lap.vertical_ratio_percent,
            }
        )

    start_time_local = ""
    if activity.start_time_local is not None:
        start_time_local = activity.start_time_local.isoformat()

    return {
        "type": activity.type,
        "name": activity.name,
        "activity_id": activity.garmin_activity_id,
        "start_time_local": start_time_local,
        "metrics": metrics,
        "laps": laps,
    }


def _build_context_from_raw(
    processor: DataProcessor,
    raw_activities_new: List[Dict[str, Any]],
    raw_health: Optional[Dict[str, Any]],
    raw_plan: List[Dict[str, Any]],
) -> tuple[Optional[str], Optional[str], Optional[str], List[Dict[str, Any]]]:
    converted_activities = [_convert_activity_for_processor(a) for a in raw_activities_new]

    activity_md: Optional[str] = None
    if converted_activities:
        simplified = [processor.simplify_activity(a) for a in converted_activities]
        activity_md = processor.format_for_llm(simplified)

    health_md: Optional[str] = None
    if raw_health:
        health_md = processor.format_health_summary(raw_health)

    plan_md: Optional[str] = None
    if raw_plan:
        plan_md = processor.format_future_plan(raw_plan)

    return activity_md, health_md, plan_md, converted_activities


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Welcome to GarminCoach API",
        "version": "1.0.0",
        "endpoints": {
            "daily_analysis": "/api/coach/daily-analysis",
            "health": "/health",
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/coach/home-summary", response_model=HomeSummaryResponse)
async def get_home_summary_endpoint(
    openid: str,
    db: Optional[Session] = Depends(get_db_optional),
    home_summary_service: HomeSummaryService = Depends(get_home_summary_service),
):
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    wechat_user = db.query(WechatUser).filter(WechatUser.openid == openid).one_or_none()
    if not wechat_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    cached = get_home_summary(db, wechat_user_id=wechat_user.id)
    try:
        summary = home_summary_service.build_summary(
            db=db,
            wechat_user_id=wechat_user.id,
            include_ai_brief=False,
        )
        ai_brief_to_save = summary.get("ai_brief")
        if ai_brief_to_save is None and cached is not None:
            ai_brief_to_save = cached.ai_brief_json

        upsert_home_summary(
            db,
            wechat_user_id=wechat_user.id,
            latest_run_json=summary.get("latest_run"),
            week_stats_json=summary.get("week_stats"),
            month_stats_json=summary.get("month_stats"),
            ai_brief_json=ai_brief_to_save,
        )
        db.commit()

        return HomeSummaryResponse(
            latest_run=summary.get("latest_run"),
            week_stats=summary.get("week_stats"),
            month_stats=summary.get("month_stats"),
            ai_brief=ai_brief_to_save,
            updated_at=summary.get("updated_at"),
        )
    except Exception as e:
        db.rollback()
        logger.warning(f"[HomeSummary] rebuild failed, fallback to cache: {e}")
        if cached:
            return HomeSummaryResponse(
                latest_run=cached.latest_run_json,
                week_stats=cached.week_stats_json,
                month_stats=cached.month_stats_json,
                ai_brief=cached.ai_brief_json,
                updated_at=cached.updated_at.isoformat() if cached.updated_at else None,
            )
        raise HTTPException(status_code=500, detail="首页摘要生成失败")


@app.get("/api/coach/period-analysis", response_model=PeriodAnalysisResponse)
async def get_period_analysis(
    openid: str,
    period: str,  # "week" or "month"
    db: Optional[Session] = Depends(get_db_optional),
    gemini: GeminiService = Depends(get_gemini_service),
):
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    wechat_user = db.query(WechatUser).filter(WechatUser.openid == openid).one_or_none()
    if not wechat_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    from datetime import date, timedelta
    today = date.today()

    if period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "month":
        start_date = today.replace(day=1)
        end_date = today
    else:
        raise HTTPException(status_code=400, detail="无效的周期类型")

    # 获取 Garmin 凭证和 User
    from backend.app.db.crud import get_garmin_credential
    from backend.app.db.models import User, Activity, GarminDailySummary
    from sqlalchemy import func

    credential = get_garmin_credential(db, wechat_user_id=wechat_user.id)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")

    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 查询跑步数据
    runs = db.query(Activity).filter(
        Activity.user_id == user.id,
        Activity.activity_date >= start_date,
        Activity.activity_date <= end_date,
        Activity.type.ilike("%run%"),
    ).all()

    run_count = len(runs)
    total_distance = sum((r.distance_km or 0) for r in runs)
    total_duration = sum((r.duration_seconds or 0) for r in runs)
    avg_speed = None
    if run_count >= 2 and total_distance >= 5 and total_duration > 0:
        avg_speed = round(total_distance / (total_duration / 3600.0), 1)

    # 查询睡眠数据
    sleep_records = db.query(GarminDailySummary).filter(
        GarminDailySummary.user_id == user.id,
        GarminDailySummary.summary_date >= start_date,
        GarminDailySummary.summary_date <= end_date,
    ).all()

    sleep_days = 0
    total_sleep_hours = 0.0
    for rec in sleep_records:
        if rec.sleep_time_hours is not None:
            sleep_days += 1
            total_sleep_hours += rec.sleep_time_hours
        elif rec.sleep_time_seconds is not None:
            sleep_days += 1
            total_sleep_hours += rec.sleep_time_seconds / 3600.0

    avg_sleep_hours = round(total_sleep_hours / sleep_days, 1) if sleep_days > 0 else None

    # AI 分析
    ai_analysis = None
    # 周至少 1 次跑步 + 1 天睡眠，月至少 3 次跑步 + 3 天睡眠
    min_run = 1 if period == "week" else 3
    min_sleep = 1 if period == "week" else 3

    if run_count >= min_run and sleep_days >= min_sleep:
        try:
            prompt = (
                f"作为跑步教练，请分析以下数据并给出简要建议（不超过50字）：\n"
                f"周期：{period}\n"
                f"日期：{start_date} 至 {end_date}\n"
                f"跑步次数：{run_count}\n"
                f"总跑量：{total_distance:.1f}km\n"
                f"平均速度：{avg_speed or '-'} km/h\n"
                f"睡眠天数：{sleep_days}\n"
                f"平均睡眠：{avg_sleep_hours or '-'} 小时"
            )
            ai_analysis = gemini.analyze_training(prompt)
        except Exception as e:
            logger.warning(f"[PeriodAnalysis] AI analysis failed: {e}")

    return PeriodAnalysisResponse(
        period=period,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        run_count=run_count,
        total_distance_km=round(total_distance, 1),
        avg_speed_kmh=avg_speed,
        sleep_days=sleep_days,
        avg_sleep_hours=avg_sleep_hours,
        ai_analysis=ai_analysis,
    )


@app.get("/api/coach/daily-analysis", response_model=DailyAnalysisResponse)
async def get_daily_analysis(
    openid: Optional[str] = None,
    target_date: Optional[str] = None,
    force_refresh: bool = False,
    db: Optional[Session] = Depends(get_db_optional),
    report_service: ReportService = Depends(get_report_service),
):
    wechat_user_id = None
    if openid and db:
        wechat_user = db.query(WechatUser).filter(WechatUser.openid == openid).one_or_none()
        if wechat_user:
            wechat_user_id = wechat_user.id
    """
    获取每日训练分析和 AI 教练建议。
    
    流程：
    1. 获取数据：今日跑步活动、昨晚睡眠、今日身体电量/HRV、未来3天训练计划
    2. 清洗数据：使用 DataProcessor 将原始数据转化为 Markdown 格式
    3. AI 分析：将清洗后的数据发送给 GeminiService
    4. 返回结果：包含原始数据摘要和 AI 建议
    
    Args:
        target_date: 目标日期，格式 "YYYY-MM-DD"。如果不提供，使用今天。
        garmin_client: GarminClient 实例（依赖注入）
        garmin_service: GarminService 实例（依赖注入）
        processor: DataProcessor 实例（依赖注入）
        gemini: GeminiService 实例（依赖注入）
    
    Returns:
        DailyAnalysisResponse: 包含日期、原始数据摘要和 AI 建议
    """
    logger.info(f"[API] 收到分析请求: date={target_date or 'default'}")
    
    # 确定目标日期（Mock Mode 默认使用 2026-01-01）
    if target_date:
        try:
            # 验证日期格式
            datetime.strptime(target_date, "%Y-%m-%d")
            analysis_date = target_date
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的日期格式: {target_date}。请使用 YYYY-MM-DD 格式。"
            )
    else:
        # Mock Mode 默认使用 2026-01-01（有完整的 20km 跑步数据）
        analysis_date = "2026-01-01" if USE_MOCK_MODE else date.today().isoformat()

    try:
        result = report_service.build_daily_analysis(
            wechat_user_id=wechat_user_id,
            analysis_date=analysis_date,
            force_refresh=force_refresh,
            db=db,
        )
        return DailyAnalysisResponse(**result)
    
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 捕获其他未预期的错误
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
