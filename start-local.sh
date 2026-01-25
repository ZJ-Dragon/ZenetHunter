#!/bin/bash
# ============================================================
# ZenetHunter 本地启动脚本 (Linux/macOS)
# ============================================================
# 功能：
#   - 自动清理残留进程和端口
#   - 清理 Python/前端/OS 缓存
#   - 智能环境检测和依赖安装
#   - 数据库检查和自动修复
#   - 前后端一键启动
#
# 用法：
#   ./start-local.sh              # 正常启动
#   ./start-local.sh --clean      # 深度清理后启动（清理缓存）
#   ./start-local.sh --clean-all  # 完全清理后启动（包括数据库和虚拟环境）
#   sudo ./start-local.sh         # 以 root 权限启动（推荐）
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================================
# 参数解析
# ============================================================
CLEAN_MODE=false
CLEAN_ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_MODE=true
            shift
            ;;
        --clean-all)
            CLEAN_MODE=true
            CLEAN_ALL=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --clean       启动前清理缓存（Python、前端、日志等）"
            echo "  --clean-all   启动前完全清理（包括数据库和虚拟环境）"
            echo "  -h, --help    显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  ./start-local.sh              # 正常启动"
            echo "  ./start-local.sh --clean      # 清理缓存后启动"
            echo "  sudo ./start-local.sh         # 以 root 权限启动（推荐）"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# ============================================================
# 颜色定义
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# ============================================================
# 进程清理函数
# ============================================================
cleanup_old_processes() {
    print_header "清理残留进程"
    
    # 清理 uvicorn 进程
    local uvicorn_pids=$(ps aux | grep -E "uvicorn app.main|python.*app.main" | grep -v grep | awk '{print $2}')
    if [ ! -z "$uvicorn_pids" ]; then
        print_warning "发现残留的后端进程"
        for pid in $uvicorn_pids; do
            kill -KILL $pid 2>/dev/null || true
        done
        sleep 1
        print_success "后端进程已清理"
    else
        print_success "无残留后端进程"
    fi
    
    # 清理 vite 进程
    local vite_pids=$(ps aux | grep -E "vite.*ZenetHunter|node.*vite" | grep -v grep | awk '{print $2}')
    if [ ! -z "$vite_pids" ]; then
        print_warning "发现残留的前端进程"
        for pid in $vite_pids; do
            kill -KILL $pid 2>/dev/null || true
        done
        sleep 1
        print_success "前端进程已清理"
    else
        print_success "无残留前端进程"
    fi
}

# ============================================================
# 端口清理函数
# ============================================================
check_and_free_port() {
    local port=$1
    local port_name=$2
    
    if command -v lsof &> /dev/null; then
        local pids=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pids" ]; then
            print_warning "$port_name 端口 $port 被占用 (PID: $pids)"
            kill -KILL $pids 2>/dev/null || true
            sleep 1
            print_success "端口 $port 已释放"
            return 0
        fi
    fi
    
    # 备用方法：尝试绑定端口测试
    if ! python3 -c "import socket; s=socket.socket(); s.bind(('', $port)); s.close()" 2>/dev/null; then
        print_warning "$port_name 端口 $port 可能被占用"
        sleep 1
    fi
    
    print_success "端口 $port 可用"
    return 0
}

# ============================================================
# 缓存清理函数
# ============================================================
clean_caches() {
    print_header "清理缓存"
    
    # 1. Python 缓存
    echo "  清理 Python 缓存..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type f -name "*.pyd" -delete 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "build" -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "dist" -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
    print_success "Python 缓存已清理"
    
    # 2. 前端缓存
    if [ -d "frontend" ]; then
        echo "  清理前端缓存..."
        rm -rf frontend/dist 2>/dev/null || true
        rm -rf frontend/.vite 2>/dev/null || true
        rm -rf frontend/.cache 2>/dev/null || true
        rm -rf frontend/node_modules/.cache 2>/dev/null || true
        find frontend -name "*.tsbuildinfo" -delete 2>/dev/null || true
        find frontend -name ".eslintcache" -delete 2>/dev/null || true
        print_success "前端缓存已清理"
    fi
    
    # 3. 日志文件
    echo "  清理日志文件..."
    find . -type f -name "*.log" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    find . -type f -name "*.log.*" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    rm -f /tmp/zenethunter-*.log 2>/dev/null || true
    print_success "日志文件已清理"
    
    # 4. OS 缓存
    echo "  清理系统缓存..."
    find . -name ".DS_Store" -delete 2>/dev/null || true
    find . -name "Thumbs.db" -delete 2>/dev/null || true
    find . -name "desktop.ini" -delete 2>/dev/null || true
    print_success "系统缓存已清理"
    
    # 5. IDE 缓存
    echo "  清理 IDE 缓存..."
    find . -type f -name "*.swp" -delete 2>/dev/null || true
    find . -type f -name "*.swo" -delete 2>/dev/null || true
    print_success "IDE 缓存已清理"
    
    # 6. 数据库锁文件
    echo "  清理数据库锁文件..."
    rm -f backend/data/zenethunter.db-shm backend/data/zenethunter.db-wal 2>/dev/null || true
    print_success "数据库锁文件已清理"
}

# ============================================================
# 完全清理函数（包括数据库和虚拟环境）
# ============================================================
clean_all() {
    clean_caches
    
    print_header "深度清理（数据库和虚拟环境）"
    
    echo -e "${YELLOW}⚠ 警告: 将清理数据库和虚拟环境！${NC}"
    read -p "确认继续? (yes/no): " response
    if [ "$response" != "yes" ] && [ "$response" != "y" ]; then
        echo "已取消深度清理"
        return
    fi
    
    # 清理数据库
    echo "  清理数据库文件..."
    find . -type f -name "*.db" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    find . -type f -name "*.sqlite" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    find . -type f -name "*.sqlite3" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    print_success "数据库文件已清理"
    
    # 清理虚拟环境
    echo "  清理虚拟环境..."
    rm -rf .venv venv ENV env venv.bak env.bak 2>/dev/null || true
    rm -rf backend/.venv backend/venv 2>/dev/null || true
    print_success "虚拟环境已清理"
}

# ============================================================
# 信号处理器（优雅关闭）
# ============================================================
shutdown_handler() {
    echo ""
    print_header "正在关闭所有服务"
    
    # 终止后端进程
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo "正在关闭后端服务 (PID: $BACKEND_PID)..."
        kill -TERM $BACKEND_PID 2>/dev/null || true
        
        # 等待最多3秒
        for i in {1..6}; do
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                print_success "后端服务已优雅关闭"
                break
            fi
            sleep 0.5
        done
        
        # 如果还没关闭，强制 kill
        if kill -0 $BACKEND_PID 2>/dev/null; then
            print_warning "优雅关闭超时，强制终止..."
            kill -KILL $BACKEND_PID 2>/dev/null || true
        fi
    fi
    
    # 终止前端进程
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "正在关闭前端服务 (PID: $FRONTEND_PID)..."
        kill -TERM $FRONTEND_PID 2>/dev/null || true
        sleep 1
        kill -KILL $FRONTEND_PID 2>/dev/null || true
        print_success "前端服务已关闭"
    fi
    
    # 清理所有相关进程
    pkill -f "uvicorn app.main" 2>/dev/null || true
    pkill -f "vite.*ZenetHunter" 2>/dev/null || true
    
    print_success "清理完成"
    exit 0
}

# 注册信号处理器
trap shutdown_handler SIGINT SIGTERM EXIT

# ============================================================
# 主程序开始
# ============================================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ZenetHunter 本地启动脚本 v2.0                  ║${NC}"
echo -e "${BLUE}║    集成：清理、检测、依赖、数据库、前后端启动          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
# 步骤 1: 清理残留资源
# ============================================================
print_header "步骤 1/6: 清理残留资源"
cleanup_old_processes
check_and_free_port 8000 "后端"
check_and_free_port 5173 "前端"

# ============================================================
# 步骤 2: 清理缓存（可选）
# ============================================================
if [ "$CLEAN_MODE" = true ]; then
    print_header "步骤 2/6: 清理缓存"
    if [ "$CLEAN_ALL" = true ]; then
        clean_all
    else
        clean_caches
    fi
else
    print_header "步骤 2/6: 跳过缓存清理（使用 --clean 启用）"
fi

# ============================================================
# 步骤 3: 检查 Python 环境
# ============================================================
print_header "步骤 3/6: 检查 Python 环境"

if ! command -v python3 &> /dev/null; then
    print_error "未找到 python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
print_success "Python: $PYTHON_VERSION"

# 进入后端目录
cd backend

# 智能环境检测
IN_CONDA=false
IN_VENV=false

if [ ! -z "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
    IN_CONDA=true
    print_success "检测到 Conda 环境: $CONDA_DEFAULT_ENV"
elif [ ! -z "$VIRTUAL_ENV" ]; then
    IN_VENV=true
    print_success "检测到虚拟环境: $VIRTUAL_ENV"
elif [ -d ".venv" ]; then
    echo "发现本地虚拟环境，正在激活..."
    source .venv/bin/activate
    IN_VENV=true
    print_success "已激活虚拟环境: .venv"
else
    print_warning "未检测到虚拟环境"
    echo ""
    echo "建议使用隔离环境运行："
    echo "  选项1: conda env create -f ../environment.yml && conda activate zenethunter"
    echo "  选项2: python3 -m venv .venv && source .venv/bin/activate"
    echo ""
    read -p "是否在系统环境中继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消。请先创建虚拟环境"
        exit 1
    fi
    print_warning "将在系统环境中安装依赖"
fi

# ============================================================
# 步骤 4: 安装依赖
# ============================================================
print_header "步骤 4/6: 安装/更新依赖"

pip install -q --upgrade pip

if pip install -q -e . 2>/dev/null; then
    print_success "依赖安装完成"
else
    print_warning "editable 安装失败，尝试直接安装依赖..."
    pip install -q greenlet>=3.0.0 alembic>=1.13.0
    pip install -q -e .
    print_success "依赖安装完成（备用方式）"
fi

# ============================================================
# 步骤 5: 检查和初始化数据库
# ============================================================
print_header "步骤 5/6: 检查数据库"

# 设置 DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="sqlite+aiosqlite:///./data/zenethunter.db"
    print_success "使用默认 SQLite 数据库"
else
    print_success "使用环境变量 DATABASE_URL"
fi

# 确保 data 目录存在
mkdir -p data

# 检查数据库 schema
if [ -f "data/zenethunter.db" ]; then
    COLUMN_CHECK=$(sqlite3 data/zenethunter.db "PRAGMA table_info(devices);" 2>/dev/null | grep "active_defense_status" || echo "")
    
    if [ -z "$COLUMN_CHECK" ]; then
        print_warning "检测到数据库 schema 不匹配，正在自动修复..."
        
        sqlite3 data/zenethunter.db <<EOF 2>/dev/null || true
ALTER TABLE devices ADD COLUMN active_defense_status TEXT DEFAULT 'idle';
ALTER TABLE devices ADD COLUMN recognition_manual_override INTEGER DEFAULT 0;
ALTER TABLE devices ADD COLUMN discovery_source TEXT DEFAULT NULL;
ALTER TABLE devices ADD COLUMN freshness_score INTEGER DEFAULT NULL;
UPDATE devices SET active_defense_status = COALESCE(attack_status, 'idle') WHERE active_defense_status IS NULL OR active_defense_status = '';
EOF
        print_success "数据库 schema 已更新"
    else
        print_success "数据库 schema 正常"
    fi
else
    print_success "将在首次启动时创建数据库"
fi

# ============================================================
# 步骤 6: 启动服务
# ============================================================
print_header "步骤 6/6: 启动服务"

# 检测操作系统和权限
OS_TYPE=$(uname -s)
IS_ROOT=false
if [ "$EUID" -eq 0 ] || [ "$(id -u)" -eq 0 ]; then
    IS_ROOT=true
    print_success "检测到 root 权限，将启用所有网络功能"
else
    print_warning "当前未使用 root 权限，某些功能可能受限"
    echo "  提示: sudo ./start-local.sh"
fi

# 设置环境变量
export APP_ENV=development
export APP_HOST=0.0.0.0
export APP_PORT=8000
export LOG_LEVEL=info
export CORS_ALLOW_ORIGINS="null,http://localhost:8000,http://localhost:5173,http://127.0.0.1:5173"

# 获取本地 IP
get_local_ip() {
    if command -v ip &> /dev/null; then
        ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}' | grep -v '^$'
    elif command -v ifconfig &> /dev/null; then
        ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | awk '{print $2}' | head -1
    fi
}

LOCAL_IP=$(get_local_ip)
if [ -n "$LOCAL_IP" ]; then
    export CORS_ALLOW_ORIGINS="$CORS_ALLOW_ORIGINS,http://$LOCAL_IP:5173"
fi

# 启动前端
cd "$SCRIPT_DIR"
FRONTEND_PID=""

if command -v node &> /dev/null && command -v npm &> /dev/null; then
    if [ -d "frontend" ]; then
        cd frontend
        
        if [ ! -d "node_modules" ]; then
            echo "安装前端依赖..."
            npm install
        fi
        
        echo "启动 React 前端服务器..."
        npm run dev > /tmp/zenethunter-frontend.log 2>&1 &
        FRONTEND_PID=$!
        sleep 2
        
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            print_success "前端服务器已启动 (PID: $FRONTEND_PID, 端口: 5173)"
        else
            print_warning "前端服务器启动失败，查看: /tmp/zenethunter-frontend.log"
            FRONTEND_PID=""
        fi
        
        cd "$SCRIPT_DIR"
    fi
else
    print_warning "未找到 Node.js/npm，跳过前端服务器"
fi

# 启动后端
cd backend

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   服务启动完成                         ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  后端 API:  http://localhost:8000                      ║${NC}"
echo -e "${GREEN}║  API 文档:  http://localhost:8000/docs                 ║${NC}"
echo -e "${GREEN}║  前端页面:  http://localhost:5173                      ║${NC}"
if [ -n "$LOCAL_IP" ]; then
echo -e "${GREEN}║  网络访问:  http://$LOCAL_IP:5173                    ║${NC}"
fi
echo -e "${GREEN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  按 Ctrl+C 优雅关闭所有服务                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# 启动 uvicorn（前台运行）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

print_success "后端服务器已启动 (PID: $BACKEND_PID)"

# 等待后端进程
wait $BACKEND_PID
BACKEND_EXIT_CODE=$?
echo ""
echo "后端进程已退出 (exit code: $BACKEND_EXIT_CODE)"
