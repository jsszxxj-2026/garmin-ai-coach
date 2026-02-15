# Taro 微信小程序 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `miniapp/` 下创建 Taro 微信小程序，仅保留核心功能（首页、详细分析、历史），直连后端 API，使用原生组件 + 自定义样式。

**Architecture:** 使用 Taro React 工程结构，页面分为 `home`、`history`、`analysis`，TabBar 仅包含 `home` 与 `history`。API 层统一请求后端，页面内做轻量缓存与错误处理。

**Tech Stack:** Taro (React), TypeScript, 微信小程序, 后端 REST API。

---

### Task 1: 初始化 Taro 小程序工程

**Files:**
- Create: `miniapp/` (Taro 项目结构)

**Step 1: Write the failing test**

无（脚手架初始化）

**Step 2: Run test to verify it fails**

无

**Step 3: Write minimal implementation**

运行 Taro CLI 初始化（非交互参数优先）：

```bash
npx @tarojs/cli init miniapp --type react --name "garmin-coach-miniapp" --description "Garmin Coach Miniapp" --template react
```

如果 CLI 仍要求交互，按提示选择：
- Framework: React
- TypeScript: Yes
- CSS: Less 或 Sass（建议与默认一致）
- Template: Default (React)

**Step 4: Run test to verify it passes**

Run: `cd miniapp && npx taro build --type weapp`
Expected: build 成功

**Step 5: Commit**

```bash
git add miniapp/
git commit -m "feat: scaffold taro miniapp"
```

---

### Task 2: 配置 TabBar 与页面路由

**Files:**
- Modify: `miniapp/src/app.config.ts`
- Create: `miniapp/src/pages/home/index.tsx`
- Create: `miniapp/src/pages/history/index.tsx`
- Create: `miniapp/src/pages/analysis/index.tsx`

**Step 1: Write the failing test**

无（构建验证）

**Step 2: Run test to verify it fails**

Run: `cd miniapp && npx taro build --type weapp`
Expected: 失败（页面缺失或配置错误）

**Step 3: Write minimal implementation**

- `app.config.ts` 设置 `pages` 与 `tabBar`：
  - pages: `pages/home/index`, `pages/history/index`, `pages/analysis/index`
  - tabBar: `home` 与 `history`
- 三个页面先输出基础文本与标题。

**Step 4: Run test to verify it passes**

Run: `cd miniapp && npx taro build --type weapp`
Expected: PASS

**Step 5: Commit**

```bash
git add miniapp/src/app.config.ts miniapp/src/pages
git commit -m "feat: add miniapp pages and tabbar"
```

---

### Task 3: API 封装与基础类型

**Files:**
- Create: `miniapp/src/api/client.ts`
- Create: `miniapp/src/api/coach.ts`
- Create: `miniapp/src/types/index.ts`

**Step 1: Write the failing test**

无（构建验证）

**Step 2: Run test to verify it fails**

Run: `cd miniapp && npx taro build --type weapp`
Expected: FAIL（引用缺失）

**Step 3: Write minimal implementation**

- `client.ts`：封装 `Taro.request`，支持 base URL（从 `app.config.ts` 或 `env` 读取）。
- `coach.ts`：实现 `getDailyAnalysis`、`getDailyAnalysisByDate`、`loginWechat`、`bindGarmin`、`getProfile`、`chat`。
- `types/index.ts`：定义 `DailyAnalysisResponse`、`ChatResponse`、`ProfileResponse`。

**Step 4: Run test to verify it passes**

Run: `cd miniapp && npx taro build --type weapp`
Expected: PASS

**Step 5: Commit**

```bash
git add miniapp/src/api miniapp/src/types
git commit -m "feat: add miniapp api client and types"
```

---

### Task 4: 通用组件（Loading / Error / StatCard / MarkdownView）

**Files:**
- Create: `miniapp/src/components/Loading/index.tsx`
- Create: `miniapp/src/components/Error/index.tsx`
- Create: `miniapp/src/components/StatCard/index.tsx`
- Create: `miniapp/src/components/MarkdownView/index.tsx`
- Create: `miniapp/src/components/index.less`

**Step 1: Write the failing test**

无（构建验证）

**Step 2: Run test to verify it fails**

Run: `cd miniapp && npx taro build --type weapp`
Expected: FAIL（引用缺失）

**Step 3: Write minimal implementation**

- Loading：简单文案 + Spinner
- Error：错误信息 + 重试按钮
- StatCard：标题 + 数值 + 单位
- MarkdownView：先用 `RichText` 支持基本段落/列表（简化解析）

**Step 4: Run test to verify it passes**

Run: `cd miniapp && npx taro build --type weapp`
Expected: PASS

**Step 5: Commit**

```bash
git add miniapp/src/components
git commit -m "feat: add miniapp base components"
```

---

### Task 5: 首页（Home）与绑定入口

**Files:**
- Modify: `miniapp/src/pages/home/index.tsx`
- Create: `miniapp/src/pages/home/index.less`

**Step 1: Write the failing test**

无（构建验证）

**Step 2: Run test to verify it fails**

Run: `cd miniapp && npx taro build --type weapp`
Expected: FAIL（引用缺失）

**Step 3: Write minimal implementation**

- 页面加载调用 `getDailyAnalysis`
- 未绑定时提示并提供“绑定 Garmin”按钮（调用 `bindGarmin`）
- 展示摘要与 StatCard
- 入口按钮跳转 Analysis
- 对话入口按钮跳转 Chat（可先简单弹窗）

**Step 4: Run test to verify it passes**

Run: `cd miniapp && npx taro build --type weapp`
Expected: PASS

**Step 5: Commit**

```bash
git add miniapp/src/pages/home
git commit -m "feat: add home page with binding and summary"
```

---

### Task 6: 历史页（History）

**Files:**
- Modify: `miniapp/src/pages/history/index.tsx`
- Create: `miniapp/src/pages/history/index.less`

**Step 1: Write the failing test**

无（构建验证）

**Step 2: Run test to verify it fails**

Run: `cd miniapp && npx taro build --type weapp`
Expected: FAIL

**Step 3: Write minimal implementation**

- 生成最近 7 天日期
- 点击日期跳转 Analysis 并传 `target_date`

**Step 4: Run test to verify it passes**

Run: `cd miniapp && npx taro build --type weapp`
Expected: PASS

**Step 5: Commit**

```bash
git add miniapp/src/pages/history
git commit -m "feat: add history page"
```

---

### Task 7: 详细分析页（Analysis）

**Files:**
- Modify: `miniapp/src/pages/analysis/index.tsx`
- Create: `miniapp/src/pages/analysis/index.less`

**Step 1: Write the failing test**

无（构建验证）

**Step 2: Run test to verify it fails**

Run: `cd miniapp && npx taro build --type weapp`
Expected: FAIL

**Step 3: Write minimal implementation**

- 根据 `target_date` 拉取报告
- 使用 MarkdownView 渲染建议
- 指标卡展示关键数据

**Step 4: Run test to verify it passes**

Run: `cd miniapp && npx taro build --type weapp`
Expected: PASS

**Step 5: Commit**

```bash
git add miniapp/src/pages/analysis
git commit -m "feat: add analysis page"
```

---

### Task 8: 文档与运行说明

**Files:**
- Modify: `README.md`
- Create: `miniapp/README.md`

**Step 1: Write the failing test**

无

**Step 2: Write minimal implementation**

- 说明 miniapp 启动与构建命令
- 说明 API 地址配置方式

**Step 3: Commit**

```bash
git add README.md miniapp/README.md
git commit -m "docs: add miniapp usage guide"
```

---

Plan complete and saved to `docs/plans/2026-02-13-taro-miniapp-implementation.md`. Two execution options:

1. Subagent-Driven (this session) - I dispatch fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) - Open new session with executing-plans, batch execution with checkpoints

Which approach?
