#!/bin/bash
# 本地启动脚本 - 不使用 Docker

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== ZenetHunter 本地启动 ==="
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "提示: 建议使用虚拟环境"
    echo "创建虚拟环境: python3 -m venv .venv"
    echo "激活虚拟环境: source .venv/bin/activate"
    echo ""
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 进入后端目录
cd backend

# 检查依赖
if [ ! -d ".venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 安装依赖
echo "安装/更新依赖..."
pip install -q --upgrade pip
# 确保安装所有必需依赖，包括 greenlet（SQLAlchemy 异步必需）
pip install -q -e . || {
    echo "警告: 使用 pip install -e . 失败，尝试直接安装依赖..."
    pip install -q greenlet>=3.0.0
    pip install -q -e .
}

# 检查数据库
echo ""
echo "检查数据库配置..."
if [ -z "$DATABASE_URL" ]; then
    echo "使用默认 SQLite 数据库 (backend/data/zenethunter.db)"
    export DATABASE_URL="sqlite+aiosqlite:///./data/zenethunter.db"
else
    echo "使用环境变量 DATABASE_URL"
fi

# 检测操作系统
OS_TYPE=$(uname -s)
echo "检测到操作系统: $OS_TYPE"

# 设置环境变量
export APP_ENV=development
export APP_HOST=0.0.0.0
export APP_PORT=8000
export LOG_LEVEL=info
# CORS: 允许 React 前端（Vite 开发服务器端口 5173）和 localhost:8000（后端）
export CORS_ALLOW_ORIGINS="null,http://localhost:8000,http://localhost:5173,http://127.0.0.1:5173"

# 检测 root 权限
IS_ROOT=false
if [ "$EUID" -eq 0 ] || [ "$(id -u)" -eq 0 ]; then
    IS_ROOT=true
    echo "✓ 检测到 root 权限，将使用最高权限启动后端服务"
    echo "  这将启用所有网络扫描功能（ARP sweep、ICMP ping 等）"
else
    echo "提示: 当前未使用 root 权限运行"
    echo "提示: 某些网络功能（如 ARP sweep）可能需要 root 权限"
    echo "提示: 如需 root 权限运行: sudo $0"
fi

# macOS 特定设置（默认使用 macOS 脚本）
if [ "$OS_TYPE" = "Darwin" ]; then
    echo "✓ macOS 检测到，使用 macOS 优化配置"
    if [ "$IS_ROOT" = false ]; then
        echo "提示: 某些网络功能可能需要管理员权限 (sudo)"
        echo "提示: 如需 root 权限运行: sudo $0"
    fi
else
    echo "提示: 当前系统为 $OS_TYPE，将使用 Linux 配置"
    if [ "$IS_ROOT" = false ]; then
        echo "提示: 某些网络功能可能需要 root 权限或 NET_RAW capability"
        echo "提示: 如需 root 权限运行: sudo $0"
    fi
fi

# 获取本地 IP 地址
get_local_ip() {
    if command -v ip &> /dev/null; then
        ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}' | grep -v '^$'
    elif command -v ifconfig &> /dev/null; then
        ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | awk '{print $2}' | head -1
    else
        echo ""
    fi
}

LOCAL_IP=$(get_local_ip)

# 如果检测到本地 IP，也添加到 CORS 允许列表
if [ -n "$LOCAL_IP" ]; then
    export CORS_ALLOW_ORIGINS="$CORS_ALLOW_ORIGINS,http://$LOCAL_IP:5173"
fi

echo ""
echo "启动服务..."
echo "后端 API: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "前端页面 (React):"
echo "  - 本地访问: http://localhost:5173"
if [ -n "$LOCAL_IP" ]; then
    echo "  - 网络访问: http://$LOCAL_IP:5173"
fi
echo ""
echo "提示: React 前端服务器将在后台运行（Vite 开发服务器）"
echo "提示: CORS 已配置，允许从前端服务器访问后端 API"
echo "按 Ctrl+C 停止所有服务"
echo ""

# 启动前端服务器（React + Vite，后台运行）
cd "$SCRIPT_DIR"
FRONTEND_PID=""

# 检查 Node.js 和 npm
if ! command -v node &> /dev/null; then
    echo "警告: 未找到 Node.js，跳过前端服务器启动"
    echo "提示: 请安装 Node.js (https://nodejs.org/) 以使用 React 前端"
elif ! command -v npm &> /dev/null; then
    echo "警告: 未找到 npm，跳过前端服务器启动"
else
    # 进入前端目录
    if [ -d "frontend" ]; then
        cd frontend

        # 检查是否已安装依赖
        if [ ! -d "node_modules" ]; then
            echo "安装前端依赖..."
            npm install
        fi

        # 启动 Vite 开发服务器（后台运行）
        echo "启动 React 前端服务器..."
        npm run dev > /tmp/zenethunter-frontend.log 2>&1 &
        FRONTEND_PID=$!
        sleep 2

        # 检查进程是否还在运行
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "✓ React 前端服务器已启动 (PID: $FRONTEND_PID, 端口: 5173)"
        else
            echo "警告: 前端服务器启动失败，请检查日志: /tmp/zenethunter-frontend.log"
            FRONTEND_PID=""
        fi

        cd "$SCRIPT_DIR"
    else
        echo "警告: frontend 目录不存在，跳过前端服务器启动"
    fi
fi

# 清理函数：停止前端服务器
cleanup() {
    echo ""
    echo "正在停止服务..."
    if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "React 前端服务器已停止"
    fi
    # 也尝试通过进程名停止（备用方案）
    pkill -f "vite" 2>/dev/null || true
    exit 0
}

# 注册清理函数
trap cleanup SIGINT SIGTERM EXIT

# 启动后端（前台运行）
cd backend

# 如果检测到 root 权限，使用最高权限启动
if [ "$IS_ROOT" = true ]; then
    echo ""
    echo "使用 root 权限启动后端服务..."
    echo "警告: 正在以 root 权限运行，请确保系统安全"
    echo ""
    # 已经是 root，直接运行（不需要 sudo）
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    # 普通权限运行
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
