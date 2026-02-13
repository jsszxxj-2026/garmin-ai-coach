# AI 跑步教练（多用户 + 密码加密）Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 支持多用户 Garmin 账号绑定，30 分钟轮询检测新数据，自动生成日报并推送小程序订阅消息，支持小程序内对话与计划提醒，且 Garmin 密码加密存储。

**Architecture:**
- 小程序用户绑定独立 Garmin 账号（加密保存密码）。
- 定时轮询按用户拉取 Garmin 数据并做新数据判定。
- 有新数据则生成日报（Gemini）并写库，通过订阅消息推送。
- 小程序内提供报告查看与对话。

**Tech Stack:** FastAPI、SQLAlchemy、APScheduler/cron、google.generativeai、WeChat 小程序订阅消息 API、cryptography.fernet。

---

### Task 1: 多用户配置与密钥管理

**Files:**
- Modify: `src/core/config.py`
- Modify: `.env.example`

**Step 1: Write the failing test**

```python
def test_wechat_settings_exist():
    from src.core.config import settings

    assert hasattr(settings, "WECHAT_MINI_APPID")
    assert hasattr(settings, "WECHAT_MINI_SECRET")
    assert hasattr(settings, "WECHAT_SUBSCRIBE_TEMPLATE_ID")
    assert hasattr(settings, "GARMIN_CRED_ENCRYPTION_KEY")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL（缺字段）

**Step 3: Write minimal implementation**

新增配置项：
- `WECHAT_MINI_APPID`
- `WECHAT_MINI_SECRET`
- `WECHAT_SUBSCRIBE_TEMPLATE_ID`
- `WECHAT_SUBSCRIBE_PAGE`
- `WECHAT_TOKEN_CACHE_SECONDS`
- `GARMIN_CRED_ENCRYPTION_KEY`（Base64 或 32 字节）

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/core/config.py .env.example tests/test_config.py
git commit -m "chore: add wechat settings and garmin encryption key"
```

---

### Task 2: 加密工具封装

**Files:**
- Modify: `requirements.txt`
- Create: `backend/app/utils/crypto.py`

**Step 1: Write the failing test**

```python
def test_encrypt_roundtrip():
    from backend.app.utils.crypto import encrypt_text, decrypt_text

    plaintext = "secret"
    cipher = encrypt_text(plaintext)
    assert decrypt_text(cipher) == plaintext
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_crypto.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 使用 `cryptography.fernet`
- `encrypt_text(plain: str) -> str`
- `decrypt_text(cipher: str) -> str`
- 密钥来源 `settings.GARMIN_CRED_ENCRYPTION_KEY`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_crypto.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add requirements.txt backend/app/utils/crypto.py tests/test_crypto.py
git commit -m "feat: add encryption utilities for garmin creds"
```

---

### Task 3: 数据库模型扩展（多用户绑定）

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/db/crud.py`

**Step 1: Write the failing test**

```python
def test_wechat_user_model_exists():
    from backend.app.db.models import WechatUser  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_wechat_user_model_exists -v`
Expected: FAIL

**Step 3: Write minimal implementation**

新增模型/字段：
- `WechatUser`: `id`, `openid`, `unionid`, `created_at`, `last_active_at`
- `GarminCredential`: `id`, `wechat_user_id`, `garmin_email`, `garmin_password`(密文), `is_cn`, `created_at`, `updated_at`
- `SyncState`: `id`, `wechat_user_id`, `last_activity_id`, `last_summary_date`, `last_poll_at`
- `NotificationLog`: `id`, `wechat_user_id`, `event_type`, `event_key`, `sent_at`, `status`, `error_message`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::test_wechat_user_model_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/db/models.py backend/app/db/crud.py tests/test_models.py
git commit -m "feat: add multi-user binding models"
```

---

### Task 4: Garmin 账号绑定 API

**Files:**
- Create: `backend/app/api/wechat.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/db/crud.py`
- Modify: `backend/app/utils/crypto.py`

**Step 1: Write the failing test**

```python
def test_wechat_login_endpoint():
    from backend.app.api.wechat import router
    assert router is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_wechat_api.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

接口：
- `POST /api/wechat/login`：小程序 code -> openid
- `POST /api/wechat/bind-garmin`：校验 Garmin 登录，密码加密存库
- `POST /api/wechat/unbind-garmin`
- `GET /api/wechat/profile`：绑定状态

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_wechat_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/wechat.py backend/app/main.py backend/app/db/crud.py backend/app/utils/crypto.py tests/test_wechat_api.py
git commit -m "feat: add garmin binding endpoints"
```

---

### Task 5: 微信订阅消息服务

**Files:**
- Create: `backend/app/services/wechat_service.py`

**Step 1: Write the failing test**

```python
def test_wechat_client_token_cache():
    from backend.app.services.wechat_service import WechatService

    svc = WechatService()
    assert hasattr(svc, "get_access_token")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_wechat_service.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- `get_access_token()`（缓存）
- `send_subscribe_message(openid, data, page)`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_wechat_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/wechat_service.py tests/test_wechat_service.py
git commit -m "feat: add wechat subscribe service"
```

---

### Task 6: 报告生成服务抽离

**Files:**
- Create: `backend/app/services/report_service.py`
- Modify: `backend/app/main.py`

**Step 1: Write the failing test**

```python
def test_report_service_builds_analysis():
    from backend.app.services.report_service import ReportService

    svc = ReportService()
    assert hasattr(svc, "build_daily_analysis")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_report_service.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- `fetch_raw_data(wechat_user_id, date)`
- `build_context(...)`
- `analyze_with_gemini(...)`
- `persist_analysis(...)`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_report_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/report_service.py backend/app/main.py tests/test_report_service.py
git commit -m "refactor: extract report generation service"
```

---

### Task 7: 30 分钟轮询任务（按用户）

**Files:**
- Create: `backend/app/jobs/poll_garmin.py`
- Modify: `backend/app/jobs/scheduler.py`

**Step 1: Write the failing test**

```python
def test_poll_detects_new_activity():
    from backend.app.jobs.poll_garmin import detect_new_data

    assert detect_new_data({}, {}) is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_polling.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 查询绑定 Garmin 的用户
- 解密密码并拉取数据
- 用 `SyncState` 判定新数据
- 触发 `ReportService`
- 记录 `NotificationLog`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_polling.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/jobs/poll_garmin.py backend/app/jobs/scheduler.py tests/test_polling.py
git commit -m "feat: add multi-user polling"
```

---

### Task 8: 订阅消息模板与内容

**Files:**
- Modify: `backend/app/jobs/poll_garmin.py`

**Step 1: Write the failing test**

```python
def test_build_wechat_template_data():
    from backend.app.jobs.poll_garmin import build_template_data

    data = build_template_data("2026-01-01", "报告已生成")
    assert "thing1" in data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_wechat_template.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- `thing1`: 报告标题
- `date2`: 日期
- `thing3`: 摘要或提醒

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_wechat_template.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/jobs/poll_garmin.py tests/test_wechat_template.py
git commit -m "feat: add subscribe message payload"
```

---

### Task 9: 对话服务与后续计划提醒

**Files:**
- Create: `backend/app/services/chat_service.py`
- Modify: `backend/app/api/wechat.py`

**Step 1: Write the failing test**

```python
def test_chat_service_reply():
    from backend.app.services.chat_service import ChatService

    svc = ChatService()
    assert hasattr(svc, "reply")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_chat_service.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 读取最新日报与计划
- 生成对话回复（含明日计划提醒与恢复建议）

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_chat_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/chat_service.py backend/app/api/wechat.py tests/test_chat_service.py
git commit -m "feat: add chat service with plan hints"
```

---

### Task 10: 文档更新

**Files:**
- Modify: `README.md`
- Modify: `frontend/README.md`

**内容：**
- 多用户绑定流程
- 订阅消息模板字段
- 轮询启动方式
- 加密密钥配置说明

**Step 1: Commit**

```bash
git add README.md frontend/README.md
git commit -m "docs: add wechat multi-user mvp guide"
```

---

Plan complete and saved to `docs/plans/2026-02-13-ai-coach-wechat-mvp.md`. Two execution options:

1. Subagent-Driven (this session) - I dispatch fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) - Open new session with executing-plans, batch execution with checkpoints

Which approach? and ready to set up for implementation?
