# GarminCoach

A FastAPI-based application for integrating Garmin data with AI coaching services.

## Project Structure

```
GarminCoach/
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
├── src/                # Source code directory
│   ├── main.py        # FastAPI application entry point
│   ├── core/          # Core configuration
│   │   └── config.py  # Application configuration
│   ├── services/       # Business logic services
│   │   ├── garmin_service.py  # Garmin API integration
│   │   └── llm_service.py     # LLM API integration
│   └── models/        # Data models
└── scripts/           # Standalone scripts
    └── test_garmin_auth.py  # Garmin authentication test
```

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
# Note: After activating virtual environment, you can use 'pip' instead of 'pip3'
```

3. Copy environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` file with your actual credentials.

5. Run the application:
```bash
# 方式 1: 使用 uvicorn 运行（推荐）
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 直接运行 main.py（需要先激活虚拟环境）
source venv/bin/activate
python3 backend/app/main.py

# 方式 3: 使用虚拟环境的 Python 直接运行
./venv/bin/python3 backend/app/main.py
```

## Development

- API documentation will be available at `http://localhost:8000/docs`
- Alternative docs at `http://localhost:8000/redoc`

## Miniapp (Taro)

- 代码目录：`miniapp/`
- 开发编译：`cd miniapp && npm run dev:weapp`
- 构建：`cd miniapp && npx taro build --type weapp`
- 环境变量：在 `miniapp/.env.development` 中设置 `TARO_APP_API_BASE_URL`

## Testing

运行 Garmin 连接测试前，**必须先使用虚拟环境**（否则会报 `ModuleNotFoundError: No module named 'garminconnect'`）。

**方式一：先激活虚拟环境，再运行**
```bash
source venv/bin/activate
python3 scripts/test_garmin_auth.py
```
激活后也可用 `python`（本机若没有 `python` 命令则用 `python3`）。

**方式二：直接指定虚拟环境中的 Python（无需激活）**
```bash
./venv/bin/python3 scripts/test_garmin_auth.py
```
