# Garmin AI Coach - Web 前端示例

这是一个使用 React + TypeScript + Vite 构建的前端项目示例。

## 🚀 快速开始

### 1. 创建项目

```bash
# 使用 Vite 创建 React + TypeScript 项目
npm create vite@latest garmin-coach-frontend -- --template react-ts
cd garmin-coach-frontend

# 安装依赖
npm install
```

### 2. 安装额外依赖

```bash
# 核心依赖
npm install axios react-router-dom

# UI 和样式
npm install tailwindcss postcss autoprefixer
npm install @headlessui/react @heroicons/react

# 数据获取和状态管理
npm install @tanstack/react-query zustand

# 图表
npm install recharts

# Markdown 渲染
npm install react-markdown remark-gfm

# 日期处理
npm install date-fns
```

### 3. 配置 Tailwind CSS

```bash
npx tailwindcss init -p
```

编辑 `tailwind.config.js`:
```js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### 4. 配置环境变量

创建 `.env`:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

### 5. 运行项目

```bash
npm run dev
```

访问 http://localhost:5173

## 📁 项目结构

```
src/
├── api/              # API 调用
│   └── coach.ts
├── components/       # 组件
│   ├── DailyAnalysis.tsx
│   ├── ChartView.tsx
│   ├── HealthStats.tsx
│   └── Loading.tsx
├── pages/           # 页面
│   ├── Home.tsx
│   ├── Analysis.tsx
│   └── History.tsx
├── hooks/           # 自定义 Hooks
│   └── useDailyAnalysis.ts
├── utils/          # 工具函数
│   └── request.ts
├── types/          # TypeScript 类型
│   └── index.ts
├── App.tsx         # 根组件
└── main.tsx        # 入口文件
```

## 🎨 核心功能示例

### API 调用

```typescript
// src/api/coach.ts
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL

export interface DailyAnalysisResponse {
  date: string
  raw_data_summary: string
  ai_advice: string
  charts?: {
    labels: string[]
    paces: number[]
    heart_rates: number[]
    cadences: number[]
  }
}

export const coachApi = {
  getDailyAnalysis: async (date?: string): Promise<DailyAnalysisResponse> => {
    const response = await axios.get(`${API_BASE}/api/coach/daily-analysis`, {
      params: date ? { target_date: date } : {}
    })
    return response.data
  }
}
```

### 使用 React Query

```typescript
// src/hooks/useDailyAnalysis.ts
import { useQuery } from '@tanstack/react-query'
import { coachApi } from '../api/coach'

export function useDailyAnalysis(date?: string) {
  return useQuery({
    queryKey: ['daily-analysis', date],
    queryFn: () => coachApi.getDailyAnalysis(date),
    staleTime: 5 * 60 * 1000, // 5 分钟缓存
  })
}
```

### 组件示例

```tsx
// src/components/DailyAnalysis.tsx
import { useDailyAnalysis } from '../hooks/useDailyAnalysis'
import ReactMarkdown from 'react-markdown'
import { ChartView } from './ChartView'
import { Loading } from './Loading'

export function DailyAnalysis({ date }: { date?: string }) {
  const { data, isLoading, error } = useDailyAnalysis(date)

  if (isLoading) return <Loading />
  if (error) return <div>加载失败，请稍后重试</div>
  if (!data) return null

  return (
    <div className="space-y-6">
      {/* AI 建议 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">AI 教练建议</h2>
        <div className="prose max-w-none">
          <ReactMarkdown>{data.ai_advice}</ReactMarkdown>
        </div>
      </div>

      {/* 图表 */}
      {data.charts && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">跑步数据</h2>
          <ChartView data={data.charts} />
        </div>
      )}
    </div>
  )
}
```

## 🎯 下一步

1. 根据设计稿完善 UI
2. 添加深色模式支持
3. 添加 PWA 支持
4. 优化移动端体验
5. 添加错误处理和加载状态
