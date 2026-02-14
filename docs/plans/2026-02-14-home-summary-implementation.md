# 首页聚合摘要（home-summary）Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现后端 home-summary 聚合接口与轮询生成缓存，并在小程序首页展示最新跑步、周/月统计与 AI 简评。

**Architecture:** 在后端新增 home-summary 服务与 DB 缓存表，由轮询任务在 Garmin 数据变更时更新；新增 API `GET /api/coach/home-summary`。小程序首页调用该接口并展示摘要。Gemini 简评在轮询阶段生成并缓存。

**Tech Stack:** FastAPI, SQLAlchemy, APScheduler, google-generativeai, Taro miniapp.

---

### Task 1: 新增 home-summary 数据模型与 CRUD

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/db/crud.py`
- Test: `tests/test_home_summary.py`

**Step 1: Write the failing test**

```python
def test_home_summary_model_exists():
    from backend.app.db.models import HomeSummary  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_home_summary.py -v`
Expected: FAIL (model missing)

**Step 3: Write minimal implementation**

- 新增 `HomeSummary` 模型字段：
  - `wechat_user_id`, `latest_run_json`, `week_stats_json`, `month_stats_json`, `ai_brief_json`, `updated_at`
- CRUD：`get_home_summary`、`upsert_home_summary`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_home_summary.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/db/models.py backend/app/db/crud.py tests/test_home_summary.py
git commit -m "feat: add home summary model"
```

---

### Task 2: 聚合服务（计算最近跑步/周月统计/简评）

**Files:**
- Create: `backend/app/services/home_summary_service.py`
- Test: `tests/test_home_summary_service.py`

**Step 1: Write the failing test**

```python
def test_home_summary_insufficient_data():
    from backend.app.services.home_summary_service import HomeSummaryService
    svc = HomeSummaryService()
    assert svc.should_generate_ai_brief(run_count=0, sleep_days=0) is False
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_home_summary_service.py -v`
Expected: FAIL (service missing)

**Step 3: Write minimal implementation**

- `should_generate_ai_brief`: 近 30 天跑步 < 3 或睡眠 < 3 -> False
- `build_latest_run` / `build_week_stats` / `build_month_stats`
- `build_ai_brief`（Gemini）

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_home_summary_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/home_summary_service.py tests/test_home_summary_service.py
git commit -m "feat: add home summary service"
```

---

### Task 3: 轮询任务集成 home-summary 生成

**Files:**
- Modify: `backend/app/jobs/poll_garmin.py`

**Step 1: Write the failing test**

```python
def test_poll_updates_home_summary():
    assert True
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_poll_home_summary.py -v`
Expected: FAIL (test missing)

**Step 3: Write minimal implementation**

- 在 `poll_garmin_for_user` 新数据时调用 `HomeSummaryService.build_summary` 并缓存。

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_poll_home_summary.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/jobs/poll_garmin.py tests/test_poll_home_summary.py
git commit -m "feat: generate home summary on polling"
```

---

### Task 4: 新增 API 接口 home-summary

**Files:**
- Modify: `backend/app/main.py`
- Test: `tests/test_home_summary_api.py`

**Step 1: Write the failing test**

```python
def test_home_summary_endpoint():
    assert True
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_home_summary_api.py -v`
Expected: FAIL (route missing)

**Step 3: Write minimal implementation**

- `GET /api/coach/home-summary?openid=...`
- 读取缓存，若无则返回空结构

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_home_summary_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/main.py tests/test_home_summary_api.py
git commit -m "feat: add home summary endpoint"
```

---

### Task 5: 小程序首页展示 home-summary

**Files:**
- Modify: `miniapp/src/api/coach.ts`
- Modify: `miniapp/src/types/index.ts`
- Modify: `miniapp/src/pages/home/index.tsx`
- Test: `miniapp/tests/home.test.tsx`

**Step 1: Write the failing test**

```ts
// 追加断言 latest_run / week_stats / month_stats 渲染
```

**Step 2: Run test to verify it fails**

Run: `cd miniapp && npm test`
Expected: FAIL

**Step 3: Write minimal implementation**

- 新增 `getHomeSummary` API
- 首页展示最近跑步 + 周/月统计 + AI 简评

**Step 4: Run test to verify it passes**

Run: `cd miniapp && npm test`
Expected: PASS

**Step 5: Commit**

```bash
git add miniapp/src/api/coach.ts miniapp/src/types/index.ts miniapp/src/pages/home/index.tsx miniapp/tests/home.test.tsx
git commit -m "feat: show home summary on miniapp"
```

---

Plan complete and saved to `docs/plans/2026-02-14-home-summary-implementation.md`. Two execution options:

1. Subagent-Driven (this session) - I dispatch fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) - Open new session with executing-plans, batch execution with checkpoints

Which approach?
