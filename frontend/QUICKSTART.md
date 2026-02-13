# 🚀 快速启动指南

## 第一步：安装依赖

```bash
cd frontend
npm install
```

## 第二步：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，确保 API 地址正确
# VITE_API_BASE_URL=http://localhost:8000
```

## 第三步：启动后端 API

确保后端 API 正在运行：

```bash
# 在项目根目录
cd backend/app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或者使用 Mock Mode（无需真实 Garmin 账号）：

确保 `backend/app/main.py` 中 `USE_MOCK_MODE = True`

## 第四步：启动前端

```bash
# 在 frontend 目录
npm run dev
```

访问 http://localhost:5173

## ✅ 验证

1. 打开浏览器访问 http://localhost:5173
2. 应该能看到首页，显示今日的 AI 教练建议
3. 点击"分析"查看详细分析页面
4. 点击"历史"查看历史记录

## 🐛 常见问题

### 1. API 连接失败

**问题**：页面显示"加载失败"或网络错误

**解决**：
- 检查后端 API 是否运行在 http://localhost:8000
- 检查 `.env` 文件中的 `VITE_API_BASE_URL` 是否正确
- 检查浏览器控制台是否有 CORS 错误

### 2. 端口被占用

**问题**：`npm run dev` 报错端口 5173 被占用

**解决**：
```bash
# 修改 vite.config.ts 中的端口
server: {
  port: 5174,  # 改为其他端口
}
```

### 3. 依赖安装失败

**问题**：`npm install` 失败

**解决**：
```bash
# 清除缓存重试
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### 4. TypeScript 类型错误

**问题**：IDE 显示类型错误

**解决**：
- 确保安装了所有依赖：`npm install`
- 重启 IDE
- 运行 `npm run build` 检查是否有真实错误

## 📝 下一步

- 查看 `README.md` 了解项目结构
- 查看 `docs/frontend_options.md` 了解前端方案详情
- 开始自定义 UI 和功能！
