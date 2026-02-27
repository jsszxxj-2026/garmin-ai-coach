#!/bin/bash

# =============================================================================
# garmin-ai-coach 部署脚本
# 功能：同步 GitHub 代码并重启后端服务
# =============================================================================

# 配置
PROJECT_DIR="/var/www/garmin-ai-coach"
PORT=8000
SERVICE_NAME="garmin-ai-coach"
LOG_FILE="/var/log/${SERVICE_NAME}.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 用户运行此脚本"
    exit 1
fi

log_info "开始部署 ${SERVICE_NAME}..."

# -----------------------------------------------------------------------------
# 1. 停止当前服务
# -----------------------------------------------------------------------------
log_info "停止当前服务..."

# 查找并杀掉 uvicorn 进程
PIDS=$(ps aux | grep "uvicorn.*${SERVICE_NAME}" | grep -v grep | awk '{print $2}')
if [ -n "$PIDS" ]; then
    for pid in $PIDS; do
        log_info "杀掉进程: $pid"
        kill -9 $pid 2>/dev/null
    done
    sleep 2
else
    log_warn "没有找到运行中的 uvicorn 进程"
fi

# 也尝试通过端口查找
PORT_PIDS=$(lsof -ti:${PORT} 2>/dev/null)
if [ -n "$PORT_PIDS" ]; then
    log_info "通过端口 ${PORT} 找到进程: ${PORT_PIDS}"
    kill -9 $PORT_PIDS 2>/dev/null
    sleep 1
fi

log_info "服务已停止"

# -----------------------------------------------------------------------------
# 2. 切换到项目目录
# -----------------------------------------------------------------------------
log_info "切换到项目目录: ${PROJECT_DIR}"
cd $PROJECT_DIR || {
    log_error "无法进入项目目录: ${PROJECT_DIR}"
    exit 1
}

# -----------------------------------------------------------------------------
# 3. 拉取最新代码
# -----------------------------------------------------------------------------
log_info "从 GitHub 拉取最新代码..."
git fetch origin

# 检查是否有更新
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)

if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
    log_info "代码已是最新版本 (${LOCAL_HASH})"
else
    log_info "本地: ${LOCAL_HASH} -> 远程: ${REMOTE_HASH}"
    
    # 显示最近的提交
    log_info "最近提交:"
    git log --oneline -3 origin/main
    
    # 拉取代码
    git pull origin main
    log_info "代码同步完成"
fi

# -----------------------------------------------------------------------------
# 4. 检查并安装依赖
# -----------------------------------------------------------------------------
log_info "检查依赖..."

# 虚拟环境目录
VENV_DIR="${PROJECT_DIR}/venv"

if [ ! -d "$VENV_DIR" ]; then
    log_info "创建虚拟环境..."
    python3 -m venv $VENV_DIR
fi

# 激活虚拟环境
source $VENV_DIR/bin/activate

# 升级 pip
pip install --upgrade pip --quiet

# 安装依赖
if [ -f "${PROJECT_DIR}/requirements.txt" ]; then
    log_info "安装 Python 依赖..."
    pip install -r ${PROJECT_DIR}/requirements.txt --quiet
    log_info "依赖安装完成"
else
    log_warn "未找到 requirements.txt"
fi

# -----------------------------------------------------------------------------
# 5. 重启服务
# -----------------------------------------------------------------------------
log_info "启动后端服务..."

# 导出环境变量（如果 .env 文件存在）
if [ -f "${PROJECT_DIR}/.env" ]; then
    log_info "加载环境变量..."
    set -a
    source ${PROJECT_DIR}/.env
    set +a
fi

# 后台启动服务
cd $PROJECT_DIR
nohup python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT > $LOG_FILE 2>&1 &

# 等待服务启动
sleep 3

# 检查服务是否成功启动
if ps aux | grep -v grep | grep "uvicorn.*backend.app.main" > /dev/null; then
    log_info "服务已成功启动，端口: ${PORT}"
    
    # 显示进程信息
    ps aux | grep "uvicorn" | grep -v grep
    
    # 显示日志最后几行
    log_info "服务日志 (最后 10 行):"
    tail -n 10 $LOG_FILE
else
    log_error "服务启动失败，请检查日志: ${LOG_FILE}"
    exit 1
fi

# -----------------------------------------------------------------------------
# 6. 清理旧的 Git 引用
# -----------------------------------------------------------------------------
log_info "清理旧的 Git 引用..."
git remote prune origin > /dev/null 2>&1

# -----------------------------------------------------------------------------
# 7. 显示部署信息
# -----------------------------------------------------------------------------
echo ""
log_info "========================================="
log_info "部署完成！"
log_info "========================================="
log_info "项目目录: ${PROJECT_DIR}"
log_info "服务端口: ${PORT}"
log_info "日志文件: ${LOG_FILE}"
log_info "服务状态: $(ps aux | grep 'uvicorn.*backend.app.main' | grep -v grep | wc -l) 个进程运行中"
log_info "========================================="

exit 0
