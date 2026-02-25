#!/bin/bash

# garmin-ai-coach 后端启动脚本

# 配置
PROJECT_DIR="/var/www/garmin-ai-coach"
PORT=8000

# 进入项目目录
cd $PROJECT_DIR

# 激活虚拟环境
source venv/bin/activate

# 导出环境变量（如果 .env 文件存在）
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 启动服务
echo "启动后端服务，端口: $PORT"
exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --reload
