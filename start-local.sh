#!/bin/bash
# 本地启动脚本 - 不使用 Docker

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置信号处理器用于优雅关闭
cleanup() {
    echo ""
    echo "=== 正在关闭所有服务 ==="
    
    # 终止后端进程
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo "正在关闭后端服务 (PID: $BACKEND_PID)..."
        kill -TERM $BACKEND_PID 2>/dev/null || true
        
        # 等待最多3秒
        for i in {1..6}; do
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                echo "✅ 后端服务已优雅关闭"
                break
            fi
            sleep 0.5
        done
        
        # 如果还没关闭，强制kill
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "⚠️  优雅关闭超时，强制终止..."
            kill -KILL $BACKEND_PID 2>/dev/null || true
        fi
    fi
    
    # 终止前端进程（如果存在）
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "正在关闭前端服务 (PID: $FRONTEND_PID)..."
        kill -TERM $FRONTEND_PID 2>/dev/null || true
        sleep 1
        kill -KILL $FRONTEND_PID 2>/dev/null || true
        echo "✅ 前端服务已关闭"
    fi
    
    # 清理uvicorn子进程
    pkill -f "uvicorn app.main" 2>/dev/null || true
    
    echo "✅ 清理完成"
    exit 0
}

# 注册信号处理器
trap cleanup SIGINT SIGTERM EXIT

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

# 智能环境检测
IN_CONDA=false
IN_VENV=false

# 检测是否在conda环境中
if [ ! -z "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
    IN_CONDA=true
    echo "✓ 检测到 Conda 环境: $CONDA_DEFAULT_ENV"
    echo "  将使用当前 Conda 环境安装依赖"
elif [ ! -z "$VIRTUAL_ENV" ]; then
    IN_VENV=true
    echo "✓ 检测到虚拟环境: $VIRTUAL_ENV"
elif [ -d ".venv" ]; then
    echo "✓ 发现本地虚拟环境，正在激活..."
    source .venv/bin/activate
    IN_VENV=true
else
    echo "未检测到虚拟环境"
    echo ""
    echo "建议使用隔离环境运行，避免污染系统环境："
    echo ""
    echo "选项1（推荐）: Conda环境"
    echo "  conda env create -f ../environment.yml"
    echo "  conda activate zenethunter"
    echo "  ./start-local.sh"
    echo ""
    echo "选项2: Python虚拟环境"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  ./start-local.sh"
    echo ""
    echo "选项3: 使用系统环境（不推荐）"
    echo "  继续运行（可能污染系统Python环境）"
    echo ""
    read -p "是否在系统环境中继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消。请先创建虚拟环境或conda环境"
        exit 1
    fi
    echo "⚠️  警告：将在系统环境中安装依赖"
fi

# 安装依赖
echo ""
echo "安装/更新依赖..."

if [ "$IN_CONDA" = true ]; then
    echo "使用 Conda 环境安装依赖..."
    # 在conda环境中，优先使用conda安装，必要时使用pip
    conda install -y -q pip 2>/dev/null || true
    pip install -q --upgrade pip
    
    # 安装后端包（editable模式）
    pip install -q -e . || {
        echo "警告: editable安装失败，尝试直接安装依赖..."
        pip install -q greenlet>=3.0.0 alembic>=1.13.0
        pip install -q -e .
    }
    echo "✅ 依赖已安装到 Conda 环境: $CONDA_DEFAULT_ENV"
elif [ "$IN_VENV" = true ]; then
    echo "使用虚拟环境安装依赖..."
    pip install -q --upgrade pip
    pip install -q -e . || {
        echo "警告: editable安装失败，尝试直接安装依赖..."
        pip install -q greenlet>=3.0.0 alembic>=1.13.0
        pip install -q -e .
    }
    echo "✅ 依赖已安装到虚拟环境"
else
    echo "⚠️  在系统环境中安装依赖..."
    pip install -q --upgrade pip
    pip install -q -e . || {
        echo "警告: editable安装失败，尝试直接安装依赖..."
        pip install -q greenlet>=3.0.0 alembic>=1.13.0
        pip install -q -e .
    }
    echo "⚠️  依赖已安装到系统环境（可能污染全局Python）"
fi

# 检查和初始化数据库
echo ""
echo "检查数据库状态..."

# 设置DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "使用默认 SQLite 数据库 (backend/data/zenethunter.db)"
    export DATABASE_URL="sqlite+aiosqlite:///./data/zenethunter.db"
else
    echo "使用环境变量 DATABASE_URL"
fi

# 确保data目录存在
if [ ! -d "data" ]; then
    mkdir -p data
    echo "创建数据目录: data/"
fi

# 检查数据库文件和schema
if [ -f "data/zenethunter.db" ]; then
    echo "数据库已存在: data/zenethunter.db"
    
    # 检查是否需要迁移
    COLUMN_CHECK=$(sqlite3 data/zenethunter.db "PRAGMA table_info(devices);" 2>/dev/null | grep "active_defense_status" || echo "")
    
    if [ -z "$COLUMN_CHECK" ]; then
        echo ""
        echo "⚠️  检测到数据库schema不匹配！"
        echo "    旧schema有: attack_status, defense_status"
        echo "    新schema需要: active_defense_status"
        echo ""
        echo "正在自动修复数据库schema..."
        
        # 自动添加缺失的列
        sqlite3 data/zenethunter.db <<EOF
-- 添加新列
ALTER TABLE devices ADD COLUMN active_defense_status TEXT DEFAULT 'idle';
ALTER TABLE devices ADD COLUMN recognition_manual_override INTEGER DEFAULT 0;

-- 从旧列迁移数据
UPDATE devices SET active_defense_status = COALESCE(attack_status, 'idle') WHERE active_defense_status IS NULL OR active_defense_status = '';

-- 注意：defense_status和active_defense_policy列会保留但不再使用
EOF
        
        if [ $? -eq 0 ]; then
            echo "✅ 数据库schema已自动更新"
        else
            echo "❌ 自动更新失败"
            echo ""
            echo "手动解决方案："
            echo "  选项1（推荐）: 删除旧数据库"
            echo "    rm -rf data/zenethunter.db*"
            echo ""
            echo "  选项2: 运行Alembic迁移"
            echo "    alembic upgrade head"
            echo ""
            read -p "是否删除旧数据库并重建？(y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f data/zenethunter.db data/zenethunter.db-*
                echo "✅ 旧数据库已删除，将创建新数据库"
            else
                echo "退出。请手动解决schema问题后重新运行"
                exit 1
            fi
        fi
    else
        echo "✅ 数据库schema正常"
    fi
else
    echo "数据库不存在，将在首次启动时自动创建"
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
echo ""
if [ "$IS_ROOT" = true ]; then
    echo "使用 root 权限启动后端服务..."
    echo "警告: 正在以 root 权限运行，请确保系统安全"
else
    echo "使用普通权限启动后端服务..."
fi

# 后台启动uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo ""
echo "✅ 后端服务器已启动 (PID: $BACKEND_PID)"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "💡 按 Ctrl+C 优雅关闭（<5秒）或使用UI关闭"
echo ""

# 等待后端进程
wait $BACKEND_PID
BACKEND_EXIT_CODE=$?
echo ""
echo "后端进程已退出 (exit code: $BACKEND_EXIT_CODE)"
