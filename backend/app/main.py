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

from backend.app.services.garmin_client import GarminClient
from backend.app.services.data_processor import DataProcessor
from backend.app.services.gemini_service import GeminiService
from backend.app.db.crud import (
    get_activities_by_date,
    get_cached_analysis,
    get_daily_summary_by_date,
    get_or_create_user,
    get_training_plans_in_range,
    save_analysis,
    upsert_activities,
    upsert_daily_summary,
    upsert_training_plans,
)
from backend.app.db.session import get_db_optional, init_db
from src.services.garmin_service import GarminService
from src.core.config import settings


# 初始化 FastAPI 应用
app = FastAPI(
    title="GarminCoach API",
    description="基于 Garmin 数据和 AI 的跑步教练分析服务",
    version="1.0.0",
)


@app.on_event("startup")
def _startup() -> None:
    try:
        init_db()
    except Exception as e:
        logger.error(f"[DB] Startup init failed: {e}")

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


@app.get("/api/coach/daily-analysis", response_model=DailyAnalysisResponse)
async def get_daily_analysis(
    target_date: Optional[str] = None,
    force_refresh: bool = False,
    db: Optional[Session] = Depends(get_db_optional),
    processor: DataProcessor = Depends(get_data_processor),
    gemini: GeminiService = Depends(get_gemini_service),
):
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
    # 记录请求开始
    request_start_time = time.time()
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

    analysis_date_obj = datetime.strptime(analysis_date, "%Y-%m-%d").date()

    # ========== DB Cache ==========
    db_user_id: Optional[int] = None
    cache_hours = max(int(settings.ANALYSIS_CACHE_HOURS), 0)
    if db is not None:
        try:
            user = get_or_create_user(db, garmin_email=settings.GARMIN_EMAIL)
            db_user_id = user.id
            if not force_refresh:
                cached = get_cached_analysis(db, user_id=db_user_id, analysis_date=analysis_date_obj)
                if cached is not None:
                    is_fresh = (
                        cache_hours > 0
                        and cached.generated_at is not None
                        and (datetime.utcnow() - cached.generated_at) <= timedelta(hours=cache_hours)
                    )
                    if is_fresh:
                        logger.info(f"[DB] Fresh analysis cache hit for {analysis_date}")
                        return DailyAnalysisResponse(
                            date=analysis_date,
                            raw_data_summary=cached.raw_data_summary_md,
                            ai_advice=cached.ai_advice_md,
                            charts=cached.charts_json,
                        )
                    logger.info(f"[DB] Analysis cache stale for {analysis_date}, rebuilding")
        except Exception as e:
            logger.warning(f"[DB] Cache lookup failed, continuing without cache: {e}")
            db_user_id = None
    
    try:
        # ========== 步骤 1: 获取数据 ==========
        data_start_time = time.time()
        raw_health: Optional[Dict[str, Any]] = None
        raw_plan: List[Dict[str, Any]] = []
        raw_activities_new: List[Dict[str, Any]] = []
        data_source = "none"

        # 优先从 DB 原始数据重建，减少 Garmin 请求频率
        if not force_refresh and db is not None and db_user_id is not None:
            try:
                summary_row = get_daily_summary_by_date(db, user_id=db_user_id, summary_date=analysis_date_obj)
                activity_rows = get_activities_by_date(db, user_id=db_user_id, activity_date=analysis_date_obj)
                plan_rows = get_training_plans_in_range(
                    db,
                    user_id=db_user_id,
                    start_date=analysis_date_obj,
                    end_date=analysis_date_obj + timedelta(days=2),
                )

                if summary_row is not None:
                    raw_health = summary_row.raw_json or {
                        "date": analysis_date,
                        "sleep_time_hours": summary_row.sleep_time_hours,
                        "sleep_score": summary_row.sleep_score,
                        "body_battery": summary_row.body_battery,
                        "body_battery_charged": summary_row.body_battery_charged,
                        "body_battery_drained": summary_row.body_battery_drained,
                        "resting_heart_rate": summary_row.resting_heart_rate,
                        "average_stress_level": summary_row.average_stress_level,
                        "stress_qualifier": summary_row.stress_qualifier,
                        "hrv_status": summary_row.hrv_status,
                        "deep_sleep_seconds": summary_row.deep_sleep_seconds,
                        "rem_sleep_seconds": summary_row.rem_sleep_seconds,
                        "light_sleep_seconds": summary_row.light_sleep_seconds,
                        "awake_sleep_seconds": summary_row.awake_sleep_seconds,
                        "recovery_quality_percent": summary_row.recovery_quality_percent,
                    }

                for activity_row in activity_rows:
                    raw_activities_new.append(activity_row.raw_json or _activity_to_new_format_from_db(activity_row))

                for plan_row in plan_rows:
                    raw_plan.append(
                        plan_row.raw_json
                        or {
                            "date": plan_row.plan_date.isoformat(),
                            "workoutName": plan_row.workout_name,
                            "description": plan_row.description,
                        }
                    )

                if raw_health or raw_activities_new or raw_plan:
                    data_source = "db"
                    logger.info(f"[DB] Using stored raw data for {analysis_date}")
            except Exception as e:
                logger.warning(f"[DB] Failed to load raw data, fallback to Garmin: {e}")

        if data_source != "db":
            if USE_MOCK_MODE:
                # ========== Mock Mode: 从本地 JSON 文件读取数据 ==========
                try:
                    from backend.app.services.garmin_client import GarminClient as GC

                    mock_client = GC.__new__(GC)
                    mock_client.email = settings.GARMIN_EMAIL
                    mock_client.password = settings.GARMIN_PASSWORD
                    mock_client.is_cn = settings.GARMIN_IS_CN
                    mock_client.client = None

                    mock_activity, mock_health, mock_plan = mock_client.get_mock_data(analysis_date)
                    raw_health = mock_health
                    raw_plan = mock_plan or []
                    if mock_activity:
                        raw_activities_new = [mock_activity]
                    data_source = "mock"
                except Exception as e:
                    logger.error(f"[API] Mock 数据读取失败: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Mock 数据读取失败: {str(e)}"
                    )
            else:
                # ========== 真实模式: 从 Garmin API 获取数据 ==========
                garmin_client = get_garmin_client()
                garmin_service = get_garmin_service()

                try:
                    daily_data = garmin_service.get_daily_data(analysis_date)
                    activities = daily_data.get("activities") or []
                    if activities:
                        raw_activities_new = [a for a in activities if isinstance(a, dict)]
                except Exception:
                    raw_activities_new = []

                try:
                    health_data = garmin_client.get_health_stats(analysis_date)
                    if health_data:
                        raw_health = health_data
                except Exception:
                    raw_health = None

                try:
                    plan_data = garmin_client.get_training_plan(analysis_date, days=3)
                    if plan_data:
                        raw_plan = plan_data
                except Exception:
                    raw_plan = []

                data_source = "garmin"

        activity_md, health_md, plan_md, converted_activities = _build_context_from_raw(
            processor=processor,
            raw_activities_new=raw_activities_new,
            raw_health=raw_health,
            raw_plan=raw_plan,
        )

        data_elapsed = time.time() - data_start_time
        logger.info(f"[API] 数据获取完成，来源={data_source}，耗时 {data_elapsed:.2f}s")

        # ========== DB: Persist normalized raw data ==========
        if db is not None and db_user_id is not None and data_source in ("garmin", "mock"):
            try:
                if raw_health:
                    upsert_daily_summary(db, user_id=db_user_id, health=raw_health, summary_date=analysis_date_obj)
                if raw_activities_new:
                    upsert_activities(db, user_id=db_user_id, activities=raw_activities_new, fallback_date=analysis_date_obj)
                if raw_plan:
                    upsert_training_plans(db, user_id=db_user_id, plans=raw_plan)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"[DB] Failed to persist raw data: {e}")
        
        # ========== 步骤 2: 清洗数据 ==========
        cleaning_start_time = time.time()
        # 使用 DataProcessor 将所有数据组合成完整的日报上下文
        daily_context = processor.assemble_daily_report(
            activity_md,
            health_md,
            plan_md,
            activity_date=analysis_date,
        )
        
        cleaning_elapsed = time.time() - cleaning_start_time
        logger.info(f"[API] 数据清洗完成，耗时 {cleaning_elapsed:.2f}s")
        
        # 如果没有获取到任何数据
        if not daily_context or daily_context.strip() == "暂无数据":
            logger.warning(f"[API] 未获取到数据，返回空结果")

            empty_ai_advice = "## 📊 分析结果\n\n**提示**: 今天还没有运动数据或健康数据。请确保 Garmin 设备已同步数据。"
            if db is not None and db_user_id is not None:
                try:
                    save_analysis(
                        db,
                        user_id=db_user_id,
                        analysis_date=analysis_date_obj,
                        raw_data_summary_md="暂无数据",
                        ai_advice_md=empty_ai_advice,
                        charts_json=None,
                        model_name=getattr(gemini, "model_name", None),
                        status="no_data",
                        error_message=None,
                    )
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning(f"[DB] Failed to persist empty analysis: {e}")

            return DailyAnalysisResponse(
                date=analysis_date,
                raw_data_summary="暂无数据",
                ai_advice=empty_ai_advice,
                charts=None,
            )
        
        # ========== 步骤 3: AI 分析 ==========
        ai_start_time = time.time()
        analysis_status = "success"
        analysis_error: Optional[str] = None
        try:
            ai_advice = gemini.analyze_training(daily_context)
            ai_elapsed = time.time() - ai_start_time
            logger.info(f"[API] AI 分析完成，耗时 {ai_elapsed:.2f}s")
        except Exception as e:
            # AI 分析失败，返回友好的错误信息
            logger.error(f"[API] AI 分析失败: {str(e)}")
            analysis_status = "error"
            analysis_error = str(e)
            ai_advice = f"""## 📊 分析结果

**抱歉，AI 分析暂时不可用**

错误信息: {str(e)}

**建议**: 请稍后重试，或检查网络连接。
"""
        
        # ========== 步骤 4: 提取图表数据 ==========
        charts_data: Optional[Dict[str, List]] = None
        if converted_activities and len(converted_activities) > 0:
            # 取第一个活动提取图表数据
            first_activity = converted_activities[0]
            try:
                charts_data = processor.extract_chart_data(first_activity)
            except Exception as e:
                logger.warning(f"[API] 提取图表数据失败: {str(e)}")
                charts_data = None

        # ========== DB: Persist analysis result ==========
        if db is not None and db_user_id is not None:
            try:
                save_analysis(
                    db,
                    user_id=db_user_id,
                    analysis_date=analysis_date_obj,
                    raw_data_summary_md=daily_context,
                    ai_advice_md=ai_advice,
                    charts_json=charts_data,
                    model_name=getattr(gemini, "model_name", None),
                    status=analysis_status,
                    error_message=analysis_error,
                )
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"[DB] Failed to persist analysis: {e}")
        
        # ========== 步骤 5: 返回结果 ==========
        total_elapsed = time.time() - request_start_time
        logger.info(f"[API] 请求处理完毕，准备返回，总耗时 {total_elapsed:.2f}s")
        logger.info(f"[API] 成功打包图表数据和AI建议")
        return DailyAnalysisResponse(
            date=analysis_date,
            raw_data_summary=daily_context,
            ai_advice=ai_advice,
            charts=charts_data,
        )
    
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
