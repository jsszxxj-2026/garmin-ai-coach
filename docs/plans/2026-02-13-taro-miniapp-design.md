# Taro 微信小程序（核心功能）设计文档

**目标**：基于 Taro 构建微信小程序端，覆盖核心功能（首页、详细分析、历史），使用原生组件 + 自定义样式，直连后端 API，支持绑定、查看报告、对话入口。

---

## 架构与目录

- 新增 `miniapp/` 目录，作为独立小程序工程。
- 页面结构：
  - `home`（Tab）：今日摘要、关键指标、入口按钮
  - `history`（Tab）：最近 7 天列表
  - `analysis`（二级）：完整报告与图表/指标
- 分层：
  - `miniapp/src/api/`：封装请求
  - `miniapp/src/components/`：通用组件（Loading/Error/StatCard/MarkdownView/ChartView）
  - `miniapp/src/pages/`：页面
- TabBar：仅 `home` + `history`，`analysis` 作为普通页面跳转。

---

## 数据流与接口

- 登录与绑定：
  - `POST /api/wechat/login` -> openid
  - `POST /api/wechat/bind-garmin`
  - `GET /api/wechat/profile`
  - `POST /api/wechat/unbind-garmin`
- 首页与详情：
  - `GET /api/coach/daily-analysis`（当日）
  - `GET /api/coach/daily-analysis?target_date=YYYY-MM-DD`
- 对话：
  - `POST /api/wechat/chat`
- 前端不轮询，后端定时轮询并推送订阅消息。

---

## 组件与页面

- Home：摘要 + 指标卡 + 进入详情 + 对话入口
- Analysis：Markdown 建议 + 指标/简易图表（先降级为指标卡）
- History：近 7 天列表 + 跳转详情
- 组件：Loading / Error / StatCard / MarkdownView / ChartView（后续可扩展）

---

## 错误处理与测试

- 网络错误与服务端错误统一显示 Error 组件。
- 未绑定 Garmin 显示引导提示。
- Markdown/图表渲染失败降级为文本或提示。
- 测试策略：
  - 手动冒烟流程（登录/绑定/首页/历史/详情/对话）
  - 构建检查：`taro build --type weapp`
  - 类型检查：`tsc --noEmit`

---

## 待确认

- miniapp API 地址配置方式（env 或 app.config.ts）
- 详细分析页图表是否引入 `taro-charts`
