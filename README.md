# garmin-ai-coach

一款基于微信小程序的 AI 跑步教练应用，深度整合 Garmin 运动数据与 Google Gemini AI 能力，为跑者提供个性化的训练分析与智能建议。

## 项目简介

## 核心功能

### 🏃 运动数据同步
- 自动同步 Garmin 跑步活动（距离，配速，心率、步频等）
- 同步睡眠数据（睡眠时长、睡眠分数、深度睡眠等）
- 每 30 分钟自动轮询更新

### 🤖 AI 智能分析
- **每日报告**：基于当日运动与身体状态生成个性化建议
- **周期统计**：周/月跑量、均速、睡眠情况汇总
- **智能简评**：AI 教练针对训练数据给出专业点评（需满足数据门槛）

### 📱 微信小程序
- 扫码绑定 Garmin 账号
- 首页展示：最近跑步、周/月统计、AI 简评
- 点击卡片查看详细分析
- 支持解绑与重新绑定

## 技术架构

| 层级 | 技术栈 |
|------|--------|
| 前端 | Taro + React + TypeScript |
| 后端 | FastAPI + Python 3.9+ |
| 数据库 | MySQL + SQLAlchemy |
| AI | Google Gemini |
| 运动数据 | Garmin Connect API |

## 快速开始

### 后端
```bash
# 安装依赖
pip3 install -r requirements.txt

# 配置环境变量（参考 .env.example）
cp .env.example .env

# 启动服务
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 小程序
```bash
cd miniapp
npm install
npm run dev:weapp
```

## 主要接口

| 接口 | 说明 |
|------|------|
| `GET /api/coach/home-summary` | 首页聚合摘要 |
| `GET /api/coach/period-analysis` | 周/月统计与分析 |
| `GET /api/coach/daily-analysis` | 每日详细报告 |
| `POST /api/wechat/bind-garmin` | 绑定 Garmin 账号 |
| `POST /api/wechat/chat` | AI 教练对话 |

## 项目结构

```
garmin-ai-coach/
├── .env.example          # 环境变量模板
├── .gitignore           # Git 忽略规则
├── requirements.txt     # Python 依赖
├── README.md            # 项目文档
├── backend/             # 后端代码
│   ├── app/
│   │   ├── api/        # API 路由
│   │   ├── db/         # 数据库模型与 CRUD
│   │   ├── jobs/       # 定时任务
│   │   ├── services/   # 业务逻辑服务
│   │   └── main.py     # FastAPI 入口
│   └── app.egg-info/
├── miniapp/             # 微信小程序（Taro）
│   ├── src/
│   │   ├── api/        # API 调用
│   │   ├── components/ # 组件
│   │   ├── pages/      # 页面
│   │   └── types/      # 类型定义
│   └── dist/           # 编译输出
├── src/                 # 共享代码
│   ├── core/           # 核心配置
│   └── services/        # 共享服务
├── scripts/             # 独立脚本
├── tests/               # 测试
└── docs/               # 文档
```

## 配置说明

### 后端环境变量

```
# Garmin 配置
GARMIN_EMAIL=你的Garmin邮箱
GARMIN_PASSWORD=你的Garmin密码
GARMIN_IS_CN=true  # 中国区账号设为 true

# Gemini AI 配置
GEMINI_API_KEY=你的Gemini_API_Key

# 微信小程序配置
WECHAT_MINI_APPID=你的AppID
WECHAT_MINI_SECRET=你的AppSecret

# 加密密钥（用于存储 Garmin 密码）
GARMIN_CRED_ENCRYPTION_KEY=生成的密钥

# 数据库
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/garmin_coach
```

### 小程序环境变量

在 `miniapp/.env.development` 中设置：
```
TARO_APP_API_BASE_URL=http://你的服务器IP:8000
```

## 开发

- API 文档：http://localhost:8000/docs
- 备用文档：http://localhost:8000/redoc

## 部署

详见项目文档或部署指南。

## 测试

运行 Garmin 连接测试前，**必须先使用虚拟环境**：

```bash
# 方式一：先激活虚拟环境
source venv/bin/activate
python3 scripts/test_garmin_auth.py

# 方式二：直接指定虚拟环境中的 Python
./venv/bin/python3 scripts/test_garmin_auth.py
```
