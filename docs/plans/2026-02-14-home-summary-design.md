# 首页聚合摘要（home-summary）设计文档

**目标**：在 Garmin 数据变更时生成“首页聚合摘要”，包含最近一次跑步、当周/当月统计与简短 AI 评价，并提供后端接口供小程序首页展示。

---

## 架构与数据流

- 新增接口：`GET /api/coach/home-summary?openid=...`
- 生成时机：在 Garmin 轮询检测到数据变更时生成并缓存。
- 数据来源：
  - 最近跑步：最近一次跑步活动
  - 周/月统计：自然周、自然月内跑步活动聚合
  - 简短评价：Gemini 生成，写缓存
- 前端只读该接口，不做复杂聚合。

---

## 返回结构（示例）

```json
{
  "latest_run": {
    "start_time": "2026-02-14T07:30:00",
    "distance_km": 8.2,
    "intensity": "中等",
    "avg_pace": "5:20",
    "duration_min": 44
  },
  "week_stats": {
    "distance_km": 24.5,
    "avg_speed_kmh": 11.2
  },
  "month_stats": {
    "distance_km": 72.3,
    "avg_speed_kmh": 10.8
  },
  "ai_brief": {
    "week": "本周跑量稳定，睡眠质量中上，建议保持周中轻松跑。",
    "month": "本月总体负荷良好，注意在高强度日后增加恢复。"
  },
  "updated_at": "2026-02-14T08:00:00"
}
```

---

## 数据不足判定

- 最近一次跑步：过去 30 天内无跑步活动或缺少距离/时长 -> `latest_run = null`
- 周/月统计：窗口内跑步次数 < 2 或总距离 < 5km -> `avg_speed_kmh = null`
- 简短评价：近 30 天睡眠记录 < 3 或跑步次数 < 3 -> `ai_brief.week/month = null`

---

## 错误处理

- Gemini 失败：仅置空 `ai_brief`，其余统计照常返回。
- Garmin 拉取失败：不覆盖已有缓存。
- 统一 snake_case 输出，字段缺失用 `null`。

---

## 测试建议

- 数据不足场景：简评为空
- 有效数据场景：简评生成（mock Gemini）
- 轮询更新缓存生效
- 接口冒烟：`GET /api/coach/home-summary?openid=...`
