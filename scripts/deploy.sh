#!/bin/bash
# ============================================================
# Buyer Radar MVP - Linux Deployment Script
# ============================================================
set -e

echo "=============================================="
echo "  Buyer Radar MVP - 部署脚本"
echo "=============================================="

# --- Config ---
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_DIR="$PROJECT_DIR/database"
LOG_DIR="$PROJECT_DIR/logs"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
APP_ENV="${APP_ENV:-production}"

# --- Pre-flight checks ---
echo "[1/5] 环境检查..."
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "⚠️ npm not found, skipping frontend build"; }

# --- Create dirs ---
mkdir -p "$DB_DIR" "$LOG_DIR"

# --- Install deps ---
echo "[2/5] 安装Python依赖..."
pip3 install -r "$PROJECT_DIR/requirements.txt" -q 2>&1 | tail -2

# --- Build frontend ---
if command -v npm >/dev/null 2>&1; then
    echo "[3/5] 构建前端..."
    cd "$PROJECT_DIR/frontend"
    npm install --silent 2>&1 | tail -1
    npm run build 2>&1 | tail -3
    cd "$PROJECT_DIR"
fi

# --- Init database ---
echo "[4/5] 初始化数据库..."
cd "$PROJECT_DIR"
python3 -c "
import sys; sys.path.insert(0, 'backend')
from services.database import get_conn
with get_conn() as conn:
    conn.execute('SELECT COUNT(*) FROM buyers')
print('✅ 数据库就绪')
"

# --- Start ---
echo "[5/5] 启动服务 (HOST=$HOST PORT=$PORT)..."
cd "$PROJECT_DIR"
nohup python3 backend/main.py > "$LOG_DIR/backend.log" 2>&1 &
PID=$!
echo $PID > "$LOG_DIR/backend.pid"
echo "✅ 服务已启动 (PID=$PID)"
echo "   访问地址: http://$HOST:$PORT"

echo "=============================================="
echo "  部署完成"
echo "=============================================="