# Garmin AI Coach - Web 前端

基于 React + TypeScript + Vite 构建的 Garmin AI Coach 前端应用。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env`，设置 API 地址：

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 4. 构建生产版本

```bash
npm run build
```

构建产物在 `dist` 目录。

## 📁 项目结构

```
frontend/
├── src/
│   ├── api/              # API 调用
│   │   └── coach.ts
│   ├── components/       # 组件
│   │   ├── Layout.tsx
│   │   ├── Loading.tsx
│   │   ├── Error.tsx
│   │   ├── ChartView.tsx
│   │   └── MarkdownView.tsx
│   ├── hooks/           # 自定义 Hooks
│   │   └── useDailyAnalysis.ts
│   ├── pages/           # 页面
│   │   ├── Home.tsx
│   │   ├── Analysis.tsx
│   │   └── History.tsx
│   ├── types/           # TypeScript 类型
│   │   └── index.ts
│   ├── App.tsx          # 根组件
│   ├── main.tsx         # 入口文件
│   └── index.css        # 全局样式
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 🎨 功能特性

- ✅ **响应式设计**：适配 PC、平板、手机
- ✅ **数据可视化**：使用 Recharts 展示跑步数据图表
- ✅ **Markdown 渲染**：渲染 AI 教练建议
- ✅ **数据缓存**：使用 React Query 缓存 API 响应
- ✅ **路由导航**：多页面应用，支持历史记录查看
- ✅ **错误处理**：友好的错误提示和重试机制

## 🛠️ 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **React Router** - 路由管理
- **React Query** - 数据获取和缓存
- **Recharts** - 图表库
- **React Markdown** - Markdown 渲染
- **Axios** - HTTP 客户端

## 📱 页面说明

### 首页 (/)
- 显示今日的 AI 教练建议
- 数据摘要

### 详细分析 (/analysis)
- 完整的 AI 教练建议
- 跑步数据图表（配速、心率、步频）
- 原始数据摘要

### 历史记录 (/history)
- 查看最近7天的分析记录
- 点击日期查看对应日期的分析

## 🔧 开发说明

### 添加新页面

1. 在 `src/pages/` 创建新组件
2. 在 `src/App.tsx` 添加路由
3. 在 `src/components/Layout.tsx` 添加导航链接（可选）

### 添加新 API

1. 在 `src/api/coach.ts` 添加 API 方法
2. 创建对应的 Hook（如 `useXXX.ts`）
3. 在组件中使用 Hook

### 样式定制

- 修改 `tailwind.config.js` 自定义主题
- 修改 `src/index.css` 添加全局样式
- 使用 Tailwind CSS 类名编写组件样式

## 🚀 部署

### Vercel 部署（推荐）

1. 安装 Vercel CLI：
```bash
npm i -g vercel
```

2. 部署：
```bash
vercel
```

### Netlify 部署

1. 安装 Netlify CLI：
```bash
npm i -g netlify-cli
```

2. 部署：
```bash
netlify deploy --prod
```

### 传统服务器部署

1. 构建：
```bash
npm run build
```

2. 将 `dist` 目录内容上传到服务器
3. 配置 Nginx 指向 `dist` 目录

## 📝 注意事项

1. **API 地址**：确保后端 API 已启动，且地址配置正确
2. **CORS**：如果 API 在不同域名，需要配置 CORS
3. **环境变量**：生产环境记得配置正确的 `VITE_API_BASE_URL`

## 📱 小程序对接说明

后端提供以下接口用于小程序：

- `POST /api/wechat/login`（获取 openid）
- `POST /api/wechat/bind-garmin`（绑定 Garmin 账号）
- `POST /api/wechat/unbind-garmin`（解绑）
- `GET /api/wechat/profile`（查询绑定状态）
- `POST /api/wechat/chat`（对话入口）

## 🔗 相关链接

- [React 文档](https://react.dev/)
- [Vite 文档](https://vitejs.dev/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [React Query 文档](https://tanstack.com/query/latest)
