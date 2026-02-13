"""
Garmin API Service
负责获取并清洗 Garmin 数据，深度提取跑步动力学和详细分段数据。
"""
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from garminconnect import Garmin

from src.core.config import settings


def _is_running(activity: dict) -> bool:
    """判断是否为跑步活动（含路跑、室内跑）。"""
    for key in ("activityTypeDTO", "activityType"):
        at = activity.get(key)
        if isinstance(at, dict) and (at.get("typeKey") or "").lower() in ("running", "treadmill_running"):
            return True
    t = activity.get("activityType")
    if isinstance(t, str) and t.lower() in ("running", "treadmill_running"):
        return True
    return False


def _format_pace(speed_mps: Optional[float]) -> str:
    """
    将米/秒转换为 `分'秒"/km` 格式（例如 5'30"/km）。
    
    Args:
        speed_mps: 速度（米/秒）
    
    Returns:
        格式化的配速字符串，如 "5'30\"/km" 或 "N/A"
    """
    if speed_mps is None or not isinstance(speed_mps, (int, float)) or speed_mps <= 0:
        return "N/A"
    try:
        # 配速 = 1000 / (60 * speed_mps) 分钟/公里
        total_seconds = 1000.0 / float(speed_mps)
        minutes = int(total_seconds // 60)
        seconds = int(round(total_seconds % 60))
        if seconds >= 60:
            seconds = 0
            minutes += 1
        return f"{minutes}'{seconds:02d}\"/km"
    except (TypeError, ZeroDivisionError, ValueError):
        return "N/A"


def _format_duration(seconds: Optional[float]) -> str:
    """
    将秒数转换为 `h小时m分` 或 `m分s秒` 格式。
    
    Args:
        seconds: 总秒数
    
    Returns:
        格式化的时长字符串，如 "1小时30分" 或 "45分30秒"
    """
    if seconds is None or not isinstance(seconds, (int, float)) or seconds < 0:
        return "N/A"
    try:
        total_seconds = int(round(float(seconds)))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"
    except (TypeError, ValueError):
        return "N/A"


def _get_sleep_details(sleep_data: Optional[Dict], user_summary: Optional[Dict]) -> Dict[str, Any]:
    """
    从睡眠数据和用户摘要中提取完整的睡眠信息。
    
    优先从 get_sleep_data 返回的 dailySleepDTO 中提取详细数据。
    包含：总时长、睡眠分数、深睡时间、REM时间、浅睡时间、清醒时间。
    计算深睡+REM占总睡眠的百分比，作为恢复质量的参考。
    
    Args:
        sleep_data: get_sleep_data 返回的数据
        user_summary: get_user_summary 返回的数据
    
    Returns:
        包含睡眠详情的字典
    """
    result: Dict[str, Any] = {
        "total_duration": None,
        "total_duration_formatted": None,
        "sleep_score": None,
        "deep_sleep_seconds": None,
        "deep_sleep_formatted": None,
        "rem_sleep_seconds": None,
        "rem_sleep_formatted": None,
        "light_sleep_seconds": None,
        "light_sleep_formatted": None,
        "awake_sleep_seconds": None,
        "awake_sleep_formatted": None,
        "recovery_quality_percent": None,  # 深睡+REM占总睡眠的百分比
    }
    
    # 优先从 sleep_data 的 dailySleepDTO 提取详细数据
    if sleep_data and isinstance(sleep_data, dict):
        dto = sleep_data.get("dailySleepDTO") or {}
        
        # 总睡眠时长
        sleep_time_sec = dto.get("sleepTimeSeconds") or sleep_data.get("sleepTimeSeconds")
        if sleep_time_sec is not None and isinstance(sleep_time_sec, (int, float)):
            result["total_duration"] = float(sleep_time_sec)
            result["total_duration_formatted"] = _format_duration(sleep_time_sec)
        
        # 睡眠分数
        scores = dto.get("sleepScores") or {}
        overall = scores.get("overall") or {}
        if isinstance(overall, dict) and "value" in overall:
            result["sleep_score"] = overall.get("value")
        elif "sleepScore" in dto:
            result["sleep_score"] = dto.get("sleepScore")
        elif "sleepScore" in sleep_data:
            result["sleep_score"] = sleep_data.get("sleepScore")
        
        # 深睡时长（秒）
        deep_sleep_sec = dto.get("deepSleepSeconds")
        if deep_sleep_sec is not None and isinstance(deep_sleep_sec, (int, float)):
            result["deep_sleep_seconds"] = float(deep_sleep_sec)
            result["deep_sleep_formatted"] = _format_duration(deep_sleep_sec)
        
        # REM 睡眠时长（秒）
        rem_sleep_sec = dto.get("remSleepSeconds")
        if rem_sleep_sec is not None and isinstance(rem_sleep_sec, (int, float)):
            result["rem_sleep_seconds"] = float(rem_sleep_sec)
            result["rem_sleep_formatted"] = _format_duration(rem_sleep_sec)
        
        # 浅睡时长（秒）
        light_sleep_sec = dto.get("lightSleepSeconds")
        if light_sleep_sec is not None and isinstance(light_sleep_sec, (int, float)):
            result["light_sleep_seconds"] = float(light_sleep_sec)
            result["light_sleep_formatted"] = _format_duration(light_sleep_sec)
        
        # 清醒时长（秒）
        awake_sleep_sec = dto.get("awakeSleepSeconds")
        if awake_sleep_sec is not None and isinstance(awake_sleep_sec, (int, float)):
            result["awake_sleep_seconds"] = float(awake_sleep_sec)
            result["awake_sleep_formatted"] = _format_duration(awake_sleep_sec)
    
    # 计算恢复质量百分比（深睡+REM占总睡眠的百分比）
    if result["total_duration"] and result["total_duration"] > 0:
        deep = result.get("deep_sleep_seconds") or 0
        rem = result.get("rem_sleep_seconds") or 0
        total = result["total_duration"]
        if total > 0:
            recovery_percent = round((deep + rem) / total * 100, 1)
            result["recovery_quality_percent"] = recovery_percent
    
    return result


def _parse_lap(lap_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析单个分段（Lap）数据。
    
    提取：Lap Index, 配速, 平均心率, 该分段的步频, 跑步动力学数据。
    
    Args:
        lap_data: 单个分段的数据字典
    
    Returns:
        清洗后的分段数据
    """
    lap: Dict[str, Any] = {
        "lap_index": None,
        "distance_km": None,
        "duration_seconds": None,
        "duration_formatted": None,
        "pace": None,
        "average_hr": None,
        "max_hr": None,
        "cadence": None,  # 步频
        "stride_length_cm": None,  # 步幅（厘米）
        "ground_contact_time_ms": None,  # 触地时间（毫秒）
        "vertical_oscillation_cm": None,  # 垂直振幅（厘米）
        "vertical_ratio_percent": None,  # 垂直比（百分比）
    }
    
    if not isinstance(lap_data, dict):
        return lap
    
    # Lap Index
    lap["lap_index"] = lap_data.get("lapIndex") or lap_data.get("lap") or lap_data.get("index")
    
    # 距离（米转公里）
    distance_m = lap_data.get("distance")
    if distance_m is not None and isinstance(distance_m, (int, float)):
        lap["distance_km"] = round(float(distance_m) / 1000, 2)
    
    # 时长
    duration = lap_data.get("duration") or lap_data.get("elapsedDuration")
    if duration is not None and isinstance(duration, (int, float)):
        lap["duration_seconds"] = float(duration)
        lap["duration_formatted"] = _format_duration(duration)
    
    # 配速（从 averageSpeed 计算）
    avg_speed = lap_data.get("averageSpeed") or lap_data.get("averageMovingSpeed")
    if avg_speed is not None and isinstance(avg_speed, (int, float)) and avg_speed > 0:
        lap["pace"] = _format_pace(float(avg_speed))
    else:
        # 备选：从 pace_min_per_km 转换
        pace_min = lap_data.get("pace_min_per_km")
        if pace_min is not None and isinstance(pace_min, (int, float)) and pace_min > 0:
            total_seconds = float(pace_min) * 60
            minutes = int(total_seconds // 60)
            seconds = int(round(total_seconds % 60))
            if seconds >= 60:
                seconds = 0
                minutes += 1
            lap["pace"] = f"{minutes}'{seconds:02d}\"/km"
    
    # 心率
    avg_hr = lap_data.get("averageHR") or lap_data.get("avgHR")
    if avg_hr is not None and isinstance(avg_hr, (int, float)):
        lap["average_hr"] = int(avg_hr)
    
    max_hr = lap_data.get("maxHR") or lap_data.get("maxHeartRate")
    if max_hr is not None and isinstance(max_hr, (int, float)):
        lap["max_hr"] = int(max_hr)
    
    # 步频（cadence）
    cadence = (
        lap_data.get("averageRunCadence")
        or lap_data.get("avgRunCadence")
        or lap_data.get("runCadence")
    )
    if cadence is not None and isinstance(cadence, (int, float)):
        lap["cadence"] = int(round(float(cadence)))
    
    # 步幅（strideLength，单位可能是米或厘米）
    stride_length = lap_data.get("strideLength")
    if stride_length is not None and isinstance(stride_length, (int, float)) and stride_length > 0:
        # 如果小于 2，可能是米，转换为厘米；否则假设已经是厘米
        if stride_length < 2:
            lap["stride_length_cm"] = round(float(stride_length) * 100, 1)
        else:
            lap["stride_length_cm"] = round(float(stride_length), 1)
    
    # 触地时间（毫秒）
    gct = lap_data.get("groundContactTime")
    if gct is not None and isinstance(gct, (int, float)):
        lap["ground_contact_time_ms"] = int(round(float(gct)))
    
    # 垂直振幅（厘米）
    vo = lap_data.get("verticalOscillation")
    if vo is not None and isinstance(vo, (int, float)):
        lap["vertical_oscillation_cm"] = round(float(vo), 1)
    
    # 垂直比（百分比）
    vr = lap_data.get("verticalRatio")
    if vr is not None and isinstance(vr, (int, float)):
        lap["vertical_ratio_percent"] = round(float(vr), 1)
    
    return lap


def _parse_activity(activity: dict, client: Garmin) -> Dict[str, Any]:
    """
    深度解析跑步活动数据，提取高阶指标和分段详情。
    
    对于 running 活动，提取：
    - 基础：距离、时长、平均心率、最大心率、卡路里
    - 效率指标：平均步频、平均步幅
    - 跑步动力学：触地时间、垂直振幅、垂直比
    - 分段数据：调用 get_activity_splits，提取每公里的详细信息
    
    Args:
        activity: 活动原始数据
        client: Garmin 客户端实例
    
    Returns:
        清洗后的活动数据字典
    """
    result: Dict[str, Any] = {
        "type": None,
        "name": None,
        "activity_id": None,
        "start_time_local": None,  # 保留运动时间
        "metrics": {},
        "laps": [],
    }
    
    if not isinstance(activity, dict):
        return result
    
    # 活动类型
    at = activity.get("activityTypeDTO") or activity.get("activityType")
    if isinstance(at, dict):
        type_key = at.get("typeKey", "")
    else:
        type_key = str(at or "")
    result["type"] = type_key
    
    # 活动名称
    result["name"] = activity.get("activityName") or activity.get("name") or ""
    
    # 活动 ID
    result["activity_id"] = activity.get("activityId")
    
    # 保留运动时间数据
    result["start_time_local"] = activity.get("startTimeLocal") or activity.get("startTimeGMT") or ""
    
    # 基础指标
    metrics: Dict[str, Any] = {}
    
    # 距离（米转公里）
    distance_m = activity.get("distance")
    if distance_m is not None and isinstance(distance_m, (int, float)):
        metrics["distance_km"] = round(float(distance_m) / 1000, 2)
    
    # 时长
    duration = activity.get("duration")
    if duration is not None and isinstance(duration, (int, float)):
        metrics["duration_seconds"] = float(duration)
        metrics["duration_formatted"] = _format_duration(duration)
    
    # 心率
    avg_hr = activity.get("averageHR") or activity.get("averageHeartRate")
    if avg_hr is not None and isinstance(avg_hr, (int, float)):
        metrics["average_hr"] = int(avg_hr)
    
    max_hr = activity.get("maxHeartRate") or activity.get("maxHR")
    if max_hr is not None and isinstance(max_hr, (int, float)):
        metrics["max_hr"] = int(max_hr)
    
    min_hr = activity.get("minHeartRate") or activity.get("minHR")
    if min_hr is not None and isinstance(min_hr, (int, float)):
        metrics["min_hr"] = int(min_hr)
    
    # 卡路里
    calories = activity.get("calories") or activity.get("totalCalories")
    if calories is not None and isinstance(calories, (int, float)):
        metrics["calories"] = int(calories)
    
    # 配速（从 averageSpeed 计算）
    avg_speed = activity.get("averageSpeed")
    if avg_speed is not None and isinstance(avg_speed, (int, float)) and avg_speed > 0:
        metrics["average_pace"] = _format_pace(float(avg_speed))
    
    # 效率指标：平均步频
    cadence = (
        activity.get("averageRunningCadenceInStepsPerMinute")
        or activity.get("averageRunningCadence")
        or activity.get("avgRunCadence")
    )
    if cadence is not None and isinstance(cadence, (int, float)):
        metrics["average_cadence"] = int(round(float(cadence)))
    
    # 效率指标：平均步幅（从 distance 和 steps 计算，或从 strideLength 获取）
    steps = activity.get("steps") or activity.get("totalSteps")
    if steps is not None and isinstance(steps, (int, float)) and steps > 0:
        if distance_m is not None and isinstance(distance_m, (int, float)) and distance_m > 0:
            stride_m = float(distance_m) / float(steps)
            metrics["average_stride_length_cm"] = round(stride_m * 100, 1)
    
    # 如果活动中有 strideLength，也尝试提取
    stride_length = activity.get("strideLength") or activity.get("averageStrideLength")
    if stride_length is not None and isinstance(stride_length, (int, float)) and stride_length > 0:
        if stride_length < 2:  # 可能是米
            metrics["average_stride_length_cm"] = round(float(stride_length) * 100, 1)
        else:  # 可能是厘米
            metrics["average_stride_length_cm"] = round(float(stride_length), 1)
    
    # 跑步动力学（如果活动数据中有）
    gct = activity.get("groundContactTime") or activity.get("averageGroundContactTime")
    if gct is not None and isinstance(gct, (int, float)):
        metrics["average_ground_contact_time_ms"] = int(round(float(gct)))
    
    vo = activity.get("verticalOscillation") or activity.get("averageVerticalOscillation")
    if vo is not None and isinstance(vo, (int, float)):
        metrics["average_vertical_oscillation_cm"] = round(float(vo), 1)
    
    vr = activity.get("verticalRatio") or activity.get("averageVerticalRatio")
    if vr is not None and isinstance(vr, (int, float)):
        metrics["average_vertical_ratio_percent"] = round(float(vr), 1)
    
    result["metrics"] = metrics
    
    # 如果是跑步活动，获取详细分段数据
    if _is_running(activity) and result["activity_id"] is not None:
        try:
            splits_raw = client.get_activity_splits(result["activity_id"])
            time.sleep(0.15)  # 避免 API 限流
            
            if splits_raw:
                # 解析分段数据
                splits_list = []
                if isinstance(splits_raw, list):
                    splits_list = splits_raw
                elif isinstance(splits_raw, dict):
                    splits_list = (
                        splits_raw.get("lapDTOs")
                        or splits_raw.get("metricSplits")
                        or splits_raw.get("splits")
                        or splits_raw.get("splitList")
                        or []
                    )
                
                # 处理每个分段
                for split_data in splits_list:
                    if isinstance(split_data, dict):
                        parsed_lap = _parse_lap(split_data)
                        if parsed_lap.get("lap_index") is not None:
                            result["laps"].append(parsed_lap)
                
                # 按 lap_index 排序
                result["laps"].sort(key=lambda x: x.get("lap_index") or 0)
        
        except Exception as e:
            # 分段数据获取失败不影响整体数据
            pass
    
    return result


class GarminService:
    """获取并清洗 Garmin 数据的服务，深度提取跑步动力学和详细分段数据。"""

    def __init__(self, email: str, password: str):
        """
        初始化 Garmin 客户端并登录。
        
        Args:
            email: Garmin 邮箱
            password: Garmin 密码
        """
        self._client = Garmin(email, password, is_cn=settings.GARMIN_IS_CN)
        self._client.login()

    def get_daily_data(self, date_str: str) -> Dict[str, Any]:
        """
        获取指定日期的综合数据，深度提取跑步动力学和详细分段数据。
        
        返回数据结构：
        {
            "date": "YYYY-MM-DD",
            "summary": {
                ...睡眠和身体电量数据...
            },
            "activities": [
                {
                    "type": "Running",
                    "name": "...",
                    "metrics": { ...高阶数据... },
                    "laps": [ ...分段列表... ]
                }
            ]
        }
        
        Args:
            date_str: 日期字符串，格式 "YYYY-MM-DD"
        
        Returns:
            包含日期、摘要和活动数据的字典
        """
        summary: Optional[Dict] = None
        sleep_data: Optional[Dict] = None
        activities: List[dict] = []

        def _get_summary():
            try:
                return self._client.get_user_summary(date_str)
            except Exception:
                return None

        def _get_sleep():
            try:
                return self._client.get_sleep_data(date_str)
            except Exception:
                return None

        def _get_activities():
            try:
                return self._client.get_activities_by_date(date_str, date_str) or []
            except Exception:
                return []

        # 并行获取基础数据
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_sum = ex.submit(_get_summary)
            f_sleep = ex.submit(_get_sleep)
            f_act = ex.submit(_get_activities)
            summary = f_sum.result()
            sleep_data = f_sleep.result()
            activities = f_act.result() or []

        # 提取睡眠详情
        sleep_details = _get_sleep_details(sleep_data, summary)
        
        # 构建摘要数据
        summary_data: Dict[str, Any] = {
            "sleep": sleep_details,
        }
        
        # 提取健康指标
        if summary and isinstance(summary, dict):
            # 静息心率
            rhr = summary.get("restingHeartRate")
            if rhr is not None and isinstance(rhr, (int, float)):
                summary_data["resting_heart_rate"] = int(rhr)
            
            # Body Battery
            body_battery = summary.get("bodyBatteryMostRecentValue")
            if body_battery is not None:
                summary_data["body_battery"] = body_battery
            
            # HRV Status
            hrv_status = summary.get("hrvStatus") or summary.get("hrvStatusDTO")
            if hrv_status:
                if isinstance(hrv_status, dict):
                    summary_data["hrv_status"] = hrv_status.get("status") or hrv_status.get("value")
                else:
                    summary_data["hrv_status"] = str(hrv_status)
            
            # 压力
            stress_level = (
                summary.get("averageStressLevel")
                or summary.get("stressLevel")
                or summary.get("stress")
            )
            if stress_level is not None and isinstance(stress_level, (int, float)):
                summary_data["average_stress_level"] = int(stress_level)
            
            stress_qualifier = summary.get("stressQualifier")
            if stress_qualifier:
                summary_data["stress_qualifier"] = str(stress_qualifier)

        # 处理活动数据
        parsed_activities: List[Dict[str, Any]] = []
        for activity in activities:
            try:
                parsed = _parse_activity(activity, self._client)
                if parsed.get("type") or parsed.get("name"):
                    parsed_activities.append(parsed)
            except Exception as e:
                # 单个活动解析失败不影响其他活动
                continue

        return {
            "date": date_str,
            "summary": summary_data,
            "activities": parsed_activities,
        }
