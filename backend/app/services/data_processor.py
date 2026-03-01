"""
将 Garmin 原始 JSON 数据清洗为 Gemini 容易理解的 Markdown 格式。
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta

from typing import Any, Dict, List, Optional

# 初始化 logger
logger = logging.getLogger(__name__)


def calculate_pace(speed_mps: Optional[float]) -> str:
    """
    从速度 (m/s) 计算配速，格式化为 "MM:SS" (min/km)。

    逻辑：Pace = 1000 / (60 * speed)
    处理 speed 为 0 或 None 的情况，返回 "N/A"。
    """
    if speed_mps is None or (isinstance(speed_mps, (int, float)) and speed_mps <= 0):
        return "N/A"
    try:
        total_seconds = 1000.0 / float(speed_mps)
    except (TypeError, ZeroDivisionError):
        return "N/A"
    mm = int(total_seconds // 60)
    ss = int(round(total_seconds % 60))
    if ss >= 60:
        ss = 0
        mm += 1
    return f"{mm}:{ss:02d}"


def calculate_pace_seconds(speed_mps: Optional[float]) -> Optional[float]:
    """
    从速度 (m/s) 计算配速，返回秒/公里（浮点数）。

    逻辑：Pace = 1000 / speed
    处理 speed 为 0 或 None 的情况，返回 None。

    Args:
        speed_mps: 速度（米/秒）

    Returns:
        配速（秒/公里），如果无法计算则返回 None
    """
    if speed_mps is None or (isinstance(speed_mps, (int, float)) and speed_mps <= 0):
        return None
    try:
        return 1000.0 / float(speed_mps)
    except (TypeError, ZeroDivisionError):
        return None


def _format_duration(seconds: Optional[float]) -> str:
    """将秒数格式化为 "MM:SS" 或 "H:MM:SS"。"""
    if seconds is None or (isinstance(seconds, (int, float)) and seconds < 0):
        return "N/A"
    try:
        s = float(seconds)
    except (TypeError, ValueError):
        return "N/A"
    if s >= 3600:
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(round(s % 60))
        if sec >= 60:
            sec = 0
            m += 1
        if m >= 60:
            m = 0
            h += 1
        return f"{h}:{m:02d}:{sec:02d}"
    m = int(s // 60)
    sec = int(round(s % 60))
    if sec >= 60:
        sec = 0
        m += 1
    return f"{m}:{sec:02d}"


def _extract_date(activity: Dict[str, Any]) -> str:
    """从 startTimeLocal 等提取 YYYY-MM-DD。"""
    local = activity.get("startTimeLocal") or activity.get("startTimeGMT") or ""
    if isinstance(local, str) and len(local) >= 10:
        return local[:10]
    return activity.get("date") or ""


class DataProcessor:
    """
    将 Garmin 活动 JSON 简化为核心字段，并格式化为 Markdown，便于 LLM 理解。
    """

    def simplify_activity(self, activity_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取核心字段：日期、类型、总距离(km)、总时长、平均心率、平均配速。
        重点处理 Splits：遍历 splits 数组，为每一段生成一个精简摘要，包含高阶跑姿数据。
        过滤掉不需要的字段（如 lat/lon, elevation gain/loss 的详细数据, split_summaries 等）。

        返回: date, type, distance_km, duration, duration_formatted, average_hr,
              average_pace, splits (每段: lap, pace, hr, stride_length, ground_contact_time,
              vertical_oscillation, vertical_ratio, cadence)
        """
        # 日期
        date_str = _extract_date(activity_json)

        # 类型
        at = activity_json.get("activityTypeDTO") or activity_json.get("activityType")
        type_str = (
            (at.get("typeKey", "") if isinstance(at, dict) else str(at or ""))
            or activity_json.get("type", "")
        )

        # 总距离 (m -> km)
        dist = activity_json.get("distance")
        distance_km = round(float(dist) / 1000, 2) if dist is not None and isinstance(dist, (int, float)) else 0.0

        # 总时长 (s)
        duration = activity_json.get("duration")
        duration_formatted = _format_duration(duration)

        # 平均心率
        average_hr = activity_json.get("averageHR") or activity_json.get("averageHeartRate")
        if average_hr is not None and isinstance(average_hr, (int, float)):
            average_hr = int(average_hr)
        else:
            average_hr = None

        # 平均配速：优先 averageSpeed -> calculate_pace
        average_pace = "N/A"
        speed = activity_json.get("averageSpeed")
        if speed is not None and isinstance(speed, (int, float)) and speed > 0:
            average_pace = calculate_pace(float(speed))
        else:
            # 备选：从 average_pace_min_per_km 转换
            p = activity_json.get("average_pace_min_per_km")
            if p is not None and isinstance(p, (int, float)) and p > 0:
                total_seconds = float(p) * 60
                mm = int(total_seconds // 60)
                ss = int(round(total_seconds % 60))
                if ss >= 60:
                    ss = 0
                    mm += 1
                average_pace = f"{mm}:{ss:02d}"

        # 处理 Splits：为每一段生成精简摘要
        simplified_splits: List[Dict[str, Any]] = []
        raw_splits = activity_json.get("splits") or []
        if not isinstance(raw_splits, list):
            raw_splits = []

        for i, s in enumerate(raw_splits):
            if not isinstance(s, dict):
                continue

            # 配速：优先 pace_min_per_km，否则从 duration + distance 计算
            pace_str = "N/A"
            if s.get("pace_min_per_km") is not None and isinstance(s.get("pace_min_per_km"), (int, float)) and s["pace_min_per_km"] > 0:
                total_seconds = float(s["pace_min_per_km"]) * 60
                mm = int(total_seconds // 60)
                ss = int(round(total_seconds % 60))
                if ss >= 60:
                    ss = 0
                    mm += 1
                pace_str = f"{mm}:{ss:02d}"
            else:
                dur = s.get("duration")
                d = s.get("distance")
                if dur is not None and d is not None and isinstance(dur, (int, float)) and isinstance(d, (int, float)) and float(d) > 0:
                    speed_split = float(d) / float(dur)
                    pace_str = calculate_pace(speed_split)

            # 心率
            hr = s.get("averageHR") or s.get("avgHR") or s.get("maxHR") or s.get("maxHeartRate")
            if hr is not None and isinstance(hr, (int, float)):
                hr = int(hr)
            else:
                hr = None

            # 提取高阶跑姿数据 (Running Dynamics)
            # strideLength (步幅, cm) -> float, 保留1位小数
            stride_length = s.get("strideLength")
            if stride_length is not None and isinstance(stride_length, (int, float)) and stride_length > 0:
                stride_length = round(float(stride_length), 1)
            else:
                stride_length = None

            # groundContactTime (触地时间, ms) -> int
            ground_contact_time = s.get("groundContactTime")
            if ground_contact_time is not None and isinstance(ground_contact_time, (int, float)) and ground_contact_time > 0:
                ground_contact_time = int(round(float(ground_contact_time)))
            else:
                ground_contact_time = None

            # verticalOscillation (垂直振幅, cm) -> float, 保留1位小数
            vertical_oscillation = s.get("verticalOscillation")
            if vertical_oscillation is not None and isinstance(vertical_oscillation, (int, float)) and vertical_oscillation > 0:
                vertical_oscillation = round(float(vertical_oscillation), 1)
            else:
                vertical_oscillation = None

            # verticalRatio (垂直步幅比, %) -> float, 保留1位小数
            vertical_ratio = s.get("verticalRatio")
            if vertical_ratio is not None and isinstance(vertical_ratio, (int, float)) and vertical_ratio > 0:
                vertical_ratio = round(float(vertical_ratio), 1)
            else:
                vertical_ratio = None

            # averageRunCadence (步频, spm) -> int
            cadence = s.get("averageRunCadence") or s.get("avgRunCadence") or s.get("runCadence")
            if cadence is not None and isinstance(cadence, (int, float)) and cadence > 0:
                cadence = int(round(float(cadence)))
            else:
                cadence = None

            simplified_splits.append({
                "lap": i + 1,
                "pace": pace_str,
                "hr": hr,
                "stride_length": stride_length,
                "ground_contact_time": ground_contact_time,
                "vertical_oscillation": vertical_oscillation,
                "vertical_ratio": vertical_ratio,
                "cadence": cadence,
            })

        # 保留运动时间数据
        start_time_local = activity_json.get("startTimeLocal") or activity_json.get("startTimeGMT") or ""
        
        return {
            "date": date_str,
            "type": type_str or "unknown",
            "distance_km": distance_km,
            "duration": duration,
            "duration_formatted": duration_formatted,
            "average_hr": average_hr,
            "average_pace": average_pace,
            "start_time": start_time_local,  # 保留运动时间
            "splits": simplified_splits,
        }

    def format_for_llm(self, activities_list: List[Dict[str, Any]]) -> str:
        """
        将简化后的数据转换为 Markdown 字符串，包含高阶跑姿数据。

        期望每项包含: date, type, distance_km, duration_formatted, average_pace,
                    average_hr, splits (每项含 lap, pace, hr, stride_length, ground_contact_time,
                    vertical_oscillation, vertical_ratio, cadence)。

        格式示例：
        ```markdown
        ## 2026-01-01 跑步 (10.02 km)
        - 总用时: 58:00
        - 平均配速: 5:47 /km
        - 平均心率: 145 bpm
        - 分段详情:
          - Lap 1: 5:30 /km, HR 130 | 步频 180, 步幅 85cm, 触地 240ms, 垂直振幅 6.9cm
          - Lap 2: 5:45 /km, HR 140 | 步频 178, 步幅 84cm, 触地 245ms, 垂直振幅 7.1cm
          ...
        ```
        """
        lines: List[str] = []
        for a in activities_list or []:
            date_str = a.get("date") or ""
            type_str = a.get("type") or "跑步"
            dist = a.get("distance_km")
            dist_str = f"{dist:.2f}" if isinstance(dist, (int, float)) else "—"
            dur = a.get("duration_formatted") or "N/A"
            pace = a.get("average_pace") or "N/A"
            hr = a.get("average_hr")
            hr_str = f"{hr} bpm" if hr is not None else "N/A"
            start_time = a.get("start_time") or ""

            lines.append(f"## {date_str} {type_str} ({dist_str} km)")
            if start_time:
                # 格式化时间显示（只显示日期和时间部分，去掉秒或时区）
                time_display = start_time[:16] if len(start_time) >= 16 else start_time
                lines.append(f"- 开始时间: {time_display}")
            lines.append(f"- 总用时: {dur}")
            lines.append(f"- 平均配速: {pace} /km")
            lines.append(f"- 平均心率: {hr_str}")
            splits = a.get("splits") or []
            if splits:
                lines.append("- 分段详情:")
                for s in splits:
                    lap = s.get("lap", "?")
                    p = s.get("pace", "N/A")
                    h = s.get("hr")
                    hh = f", HR {h}" if h is not None else ""
                    
                    # 构建跑姿数据字符串
                    dynamics_parts: List[str] = []
                    cad = s.get("cadence")
                    if cad is not None:
                        dynamics_parts.append(f"步频 {cad}")
                    
                    stride = s.get("stride_length")
                    if stride is not None:
                        dynamics_parts.append(f"步幅 {stride}cm")
                    
                    gct = s.get("ground_contact_time")
                    if gct is not None:
                        dynamics_parts.append(f"触地 {gct}ms")
                    
                    vo = s.get("vertical_oscillation")
                    if vo is not None:
                        dynamics_parts.append(f"垂直振幅 {vo}cm")
                    
                    vr = s.get("vertical_ratio")
                    if vr is not None:
                        dynamics_parts.append(f"垂直比 {vr}%")
                    
                    dynamics_str = " | " + ", ".join(dynamics_parts) if dynamics_parts else ""
                    lines.append(f"  - Lap {lap}: {p} /km{hh}{dynamics_str}")
            lines.append("")
        prompt = "\n".join(lines).strip()
        logger.info(f"[Data] 数据清洗完成，Prompt 长度: {len(prompt)} 字符")
        return prompt

    def format_health_summary(self, health_json: Optional[Dict[str, Any]]) -> str:
        """
        格式化健康数据为 Markdown 简报（增强版）。

        提取关键指标：
        - 睡眠: 总时长 (小时), 睡眠分数, 深睡/REM/清醒时长, 质量评价
        - 身体状态: 身体电量 (Body Battery charged/drained), 压力分数, 静息心率 (RHR)
        - HRV: HRV Status

        Args:
            health_json: 由 GarminClient.get_health_stats 返回的健康数据字典

        Returns:
            Markdown 格式的健康简报
        """
        if not health_json or not isinstance(health_json, dict):
            return "### 🏥 今日身体状态\n- 数据暂不可用"

        date_str = health_json.get("date", "")
        lines: List[str] = [f"### 🏥 今日身体状态 ({date_str})"]

        # 睡眠数据（增强）
        sleep_parts: List[str] = []
        # 优先使用 sleep_time_hours，否则从 sleep_time_seconds 计算
        sleep_hours = health_json.get("sleep_time_hours")
        if sleep_hours is None:
            sleep_time_sec = health_json.get("sleep_time_seconds")
            if sleep_time_sec is not None and isinstance(sleep_time_sec, (int, float)):
                sleep_hours = round(float(sleep_time_sec) / 3600, 1)
            else:
                # 尝试从 sleep_data 中提取
                sleep_data = health_json.get("sleep_data") or {}
                dto = sleep_data.get("dailySleepDTO") or {}
                sleep_sec = dto.get("sleepTimeSeconds")
                if sleep_sec is not None:
                    sleep_hours = round(float(sleep_sec) / 3600, 1)
        
        if sleep_hours is not None:
            sleep_parts.append(f"{sleep_hours}小时")

        sleep_score = health_json.get("sleep_score")
        if sleep_score is not None:
            sleep_parts.append(f"分数: {sleep_score}/100")

        # 睡眠质量评价（优先使用提取的 sleep_quality，否则根据分数推断）
        sleep_quality = health_json.get("sleep_quality")
        if not sleep_quality and sleep_score is not None:
            if sleep_score >= 80:
                sleep_quality = "优秀"
            elif sleep_score >= 60:
                sleep_quality = "良好"
            elif sleep_score >= 40:
                sleep_quality = "一般"
            else:
                sleep_quality = "较差"
        elif not sleep_quality:
            sleep_quality = "未知"
        
        if sleep_quality:
            sleep_parts.append(f"质量: {sleep_quality}")

        # 深睡、REM、浅睡、清醒时长（优先使用格式化后的时间）
        deep_sleep = health_json.get("deep_sleep_hh_mm") or health_json.get("deep_sleep_formatted")
        rem_sleep = health_json.get("rem_sleep_hh_mm") or health_json.get("rem_sleep_formatted")
        light_sleep = health_json.get("light_sleep_hh_mm") or health_json.get("light_sleep_formatted")
        awake_sleep = health_json.get("awake_sleep_hh_mm") or health_json.get("awake_sleep_formatted")
        
        sleep_stages: List[str] = []
        if deep_sleep and deep_sleep != "N/A":
            sleep_stages.append(f"深睡 {deep_sleep}")
        if rem_sleep and rem_sleep != "N/A":
            sleep_stages.append(f"REM {rem_sleep}")
        if light_sleep and light_sleep != "N/A":
            sleep_stages.append(f"浅睡 {light_sleep}")
        if awake_sleep and awake_sleep != "N/A":
            sleep_stages.append(f"清醒 {awake_sleep}")
        
        if sleep_parts:
            sleep_line = f"- **睡眠**: {' ('.join(sleep_parts)})"
            if sleep_stages:
                sleep_line += f" | {', '.join(sleep_stages)}"
            lines.append(sleep_line)
        
        # 如果有恢复质量百分比，也显示
        recovery_percent = health_json.get("recovery_quality_percent")
        if recovery_percent is not None:
            lines.append(f"  - **恢复质量**: 深睡+REM 占比 {recovery_percent}%")

        # 身体电量（增强：显示 charged/drained）
        body_battery = health_json.get("body_battery")
        body_battery_charged = health_json.get("body_battery_charged")
        body_battery_drained = health_json.get("body_battery_drained")
        
        if body_battery is not None:
            bb_status = ""
            if body_battery >= 70:
                bb_status = "充足"
            elif body_battery >= 50:
                bb_status = "正常"
            elif body_battery >= 30:
                bb_status = "偏低，注意休息"
            else:
                bb_status = "很低，建议充分休息"
            
            bb_parts = [f"Body Battery {body_battery}/100 ({bb_status})"]
            if body_battery_charged is not None:
                bb_parts.append(f"充电 {body_battery_charged}")
            if body_battery_drained is not None:
                bb_parts.append(f"消耗 {body_battery_drained}")
            
            lines.append(f"- **能量**: {' | '.join(bb_parts)}")

        # 静息心率和 HRV（增强）
        rhr = health_json.get("resting_heart_rate")
        hrv_status = health_json.get("hrv_status") or health_json.get("hrvStatus")
        heart_parts: List[str] = []
        if rhr is not None:
            heart_parts.append(f"RHR {rhr} bpm")
        if hrv_status:
            heart_parts.append(f"HRV {hrv_status}")
        elif hrv_status is None:
            # 如果明确为 None，显示"未检测"
            heart_parts.append("HRV 未检测")
        
        if heart_parts:
            lines.append(f"- **心脏**: {', '.join(heart_parts)}")

        # 压力（增强：使用 average_stress_level）
        stress_qualifier = health_json.get("stress_qualifier")
        stress_score = (
            health_json.get("average_stress_level")
            or health_json.get("stressScore")
            or health_json.get("average_stress")
        )
        if stress_qualifier or stress_score is not None:
            stress_parts: List[str] = []
            if stress_score is not None:
                stress_parts.append(f"平均压力 {stress_score}")
            if stress_qualifier:
                stress_parts.append(f"({stress_qualifier})")
            lines.append(f"- **压力**: {' '.join(stress_parts)}")

        return "\n".join(lines)

    def format_future_plan(self, calendar_json: List[Dict[str, Any]]) -> str:
        """
        格式化未来几天的训练计划为 Markdown。

        遍历每一天，提取 workoutName 和 description (如果有)。

        Args:
            calendar_json: 由 GarminClient.get_training_plan 返回的日历数据列表

        Returns:
            Markdown 格式的计划表
        """
        if not calendar_json or not isinstance(calendar_json, list):
            return "### 📅 未来计划\n- 暂无计划数据"

        lines: List[str] = [f"### 📅 未来 {len(calendar_json)} 天计划"]

        # 按日期排序（如果有日期字段）
        sorted_plans = sorted(
            calendar_json,
            key=lambda x: (
                x.get("date")
                or x.get("targetDate")
                or x.get("startDate")
                or x.get("calendarDate")
                or ""
            ),
        )

        # 日期标签映射
        today = datetime.now().date()
        date_labels = ["今天", "明天", "后天", "大后天"]
        date_index = 0

        for plan in sorted_plans:
            if not isinstance(plan, dict):
                continue

            # 获取日期
            plan_date_str = (
                plan.get("date")
                or plan.get("targetDate")
                or plan.get("startDate")
                or plan.get("calendarDate")
                or ""
            )
            plan_date_obj = None
            if plan_date_str:
                try:
                    plan_date_obj = datetime.strptime(str(plan_date_str)[:10], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass

            # 确定日期标签
            if plan_date_obj:
                days_diff = (plan_date_obj - today).days
                if 0 <= days_diff < len(date_labels):
                    date_label = date_labels[days_diff]
                else:
                    date_label = plan_date_str[:10]
            else:
                if date_index < len(date_labels):
                    date_label = date_labels[date_index]
                    date_index += 1
                else:
                    date_label = f"第{date_index + 1}天"
                    date_index += 1

            # 提取训练信息
            workout_name = (
                plan.get("workoutName")
                or plan.get("name")
                or plan.get("title")
                or plan.get("description")
                or ""
            )
            description = plan.get("description") or plan.get("details") or ""

            if workout_name:
                plan_text = workout_name
                if description and description != workout_name:
                    plan_text += f" ({description})"
                lines.append(f"- **{date_label}**: {plan_text}")
            elif description:
                lines.append(f"- **{date_label}**: {description}")
            else:
                # 如果没有具体信息，显示为休息日或未知
                lines.append(f"- **{date_label}**: 休息日")

        return "\n".join(lines)

    def assemble_daily_report(
        self,
        activity: Optional[str],
        health: Optional[str],
        plan: Optional[str],
        activity_date: Optional[str] = None,
    ) -> str:
        """
        将跑步表现、身体状态、未来计划三个部分组合成一个完整的 System Prompt 上下文。

        Args:
            activity: 由 format_for_llm 生成的跑步活动 Markdown
            health: 由 format_health_summary 生成的健康简报 Markdown
            plan: 由 format_future_plan 生成的训练计划 Markdown
            activity_date: 活动日期，用于显示标题（可选）

        Returns:
            组合后的完整日报 Markdown
        """
        sections: List[str] = []

        if activity:
            # 根据日期显示标题
            if activity_date:
                sections.append(f"## 🏃 {activity_date} 跑步表现")
            else:
                sections.append("## 🏃 跑步表现")
            sections.append(activity)
            sections.append("")

        if health:
            sections.append(health)
            sections.append("")

        if plan:
            sections.append(plan)
            sections.append("")

        if not sections:
            return "暂无数据"

        return "\n".join(sections).strip()

    def format_user_profile_summary(self, profile_data: Dict[str, Any]) -> Optional[str]:
        """
        将用户个人档案数据格式化为 Markdown 文本。

        Args:
            profile_data: 由 GarminClient.get_user_profile_data() 返回的用户档案数据

        Returns:
            用户档案的 Markdown 格式文本，如果无可用数据则返回 None
        """
        if not profile_data:
            return None

        lines: List[str] = []
        has_data = False

        # 身体成分
        weight = profile_data.get("weight_kg")
        bmi = profile_data.get("bmi")
        body_fat = profile_data.get("body_fat_percent")
        if weight or bmi or body_fat:
            has_data = True
            lines.append("### ⚖️ 身体成分")
            if weight:
                lines.append(f"- 体重: {weight} kg")
            if bmi:
                lines.append(f"- BMI: {bmi}")
            if body_fat:
                lines.append(f"- 体脂率: {body_fat}%")

        # 运动能力
        vo2_max = profile_data.get("vo2_max")
        max_hr = profile_data.get("max_heart_rate")
        resting_hr = profile_data.get("resting_heart_rate")
        if vo2_max or max_hr or resting_hr:
            has_data = True
            lines.append("### 💪 运动能力")
            if vo2_max:
                lines.append(f"- VO2Max: {vo2_max}")
            if max_hr:
                lines.append(f"- 最大心率: {max_hr} bpm")
            if resting_hr:
                lines.append(f"- 静息心率: {resting_hr} bpm")

        # 训练状态
        training_status = profile_data.get("training_status")
        training_effect = profile_data.get("training_effect")
        activity_effect = profile_data.get("activity_effect")
        if training_status or training_effect or activity_effect:
            has_data = True
            lines.append("### 📈 训练状态")
            if training_status:
                lines.append(f"- 状态: {training_status}")
            if training_effect:
                lines.append(f"- 训练效果: {training_effect}")
            if activity_effect:
                lines.append(f"- 活动效果: {activity_effect}")

        # 训练准备度
        readiness = profile_data.get("training_readiness")
        if readiness is not None:
            has_data = True
            lines.append("### 🎯 训练准备度")
            lines.append(f"- 准备度得分: {readiness}")

        if not has_data:
            return None

        return "\n".join(lines)

    def extract_chart_data(self, activity_json: Dict[str, Any]) -> Dict[str, List]:
        """
        从活动 JSON 中提取图表数据。

        遍历 splits 数组，提取每一公里的核心指标：
        - labels: ["1k", "2k", "3k", ...]
        - paces: 每一公里的配速（秒/公里，浮点数）
        - heart_rates: 每一公里的平均心率 (int)
        - cadences: 每一公里的平均步频 (int)

        Args:
            activity_json: 活动数据字典，应包含 splits 数组

        Returns:
            包含 labels, paces, heart_rates, cadences 的字典
        """
        labels: List[str] = []
        paces: List[float] = []
        heart_rates: List[int] = []
        cadences: List[int] = []

        splits = activity_json.get("splits") or []
        if not isinstance(splits, list):
            splits = []

        for i, split in enumerate(splits):
            if not isinstance(split, dict):
                continue

            # 标签：格式为 "1k", "2k", "3k" ...
            labels.append(f"{i + 1}k")

            # 配速：优先从 pace_min_per_km 计算，否则从 duration + distance 计算
            pace_seconds = None
            
            # 方法1: 从 pace_min_per_km 计算
            pace_min_per_km = split.get("pace_min_per_km")
            if pace_min_per_km is not None and isinstance(pace_min_per_km, (int, float)) and pace_min_per_km > 0:
                pace_seconds = float(pace_min_per_km) * 60.0
            else:
                # 方法2: 从 duration 和 distance 计算速度，再转换为配速
                duration = split.get("duration")
                distance = split.get("distance")
                if duration is not None and distance is not None:
                    if isinstance(duration, (int, float)) and isinstance(distance, (int, float)):
                        if float(duration) > 0 and float(distance) > 0:
                            speed_mps = float(distance) / float(duration)
                            pace_seconds = calculate_pace_seconds(speed_mps)
                
                # 方法3: 如果 splits 中有 averageSpeed 字段
                if pace_seconds is None:
                    avg_speed = split.get("averageSpeed")
                    if avg_speed is not None and isinstance(avg_speed, (int, float)) and avg_speed > 0:
                        pace_seconds = calculate_pace_seconds(float(avg_speed))
            
            paces.append(pace_seconds if pace_seconds is not None else 0.0)

            # 心率：提取平均心率
            hr = split.get("averageHR") or split.get("avgHR") or split.get("hr")
            if hr is not None and isinstance(hr, (int, float)):
                heart_rates.append(int(round(float(hr))))
            else:
                heart_rates.append(0)

            # 步频：提取平均步频
            cadence = (
                split.get("averageRunCadence")
                or split.get("avgRunCadence")
                or split.get("runCadence")
                or split.get("cadence")
            )
            if cadence is not None and isinstance(cadence, (int, float)):
                cadences.append(int(round(float(cadence))))
            else:
                cadences.append(0)

        return {
            "labels": labels,
            "paces": paces,
            "heart_rates": heart_rates,
            "cadences": cadences,
        }
