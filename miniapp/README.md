# Garmin Coach Miniapp

## 开发与构建

进入小程序目录：

```bash
cd "/Users/jsszxxj/Desktop/AI coach/.worktrees/miniapp/miniapp"
```

启动开发编译（自动增量输出到 `dist/`）：

```bash
npm run dev:weapp
```

构建生产包：

```bash
npx taro build --type weapp
```

运行单元测试：

```bash
npm test
```

## 环境变量

在 `miniapp/` 下创建 `.env.development`：

```
TARO_APP_API_BASE_URL=http://localhost:8000
```

如使用真实服务，替换为你的后端地址。

## 微信开发者工具导入

- 项目目录：`/Users/jsszxxj/Desktop/AI coach/.worktrees/miniapp/miniapp`
- 小程序目录：`dist/`

## 关键接口

- `GET /api/coach/daily-analysis`
- `POST /api/wechat/login`
- `GET /api/wechat/profile?openid=...`
- `POST /api/wechat/bind-garmin`
- `POST /api/wechat/unbind-garmin`
- `POST /api/wechat/chat`
