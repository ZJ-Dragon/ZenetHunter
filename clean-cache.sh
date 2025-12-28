#!/bin/bash
# ZenetHunter 缓存清理脚本 (Linux/macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "ZenetHunter 缓存清理工具 (Shell 版本)"
echo "============================================================"
echo "项目目录: $SCRIPT_DIR"
echo ""

# 检查参数
CLEAN_DB=false
CLEAN_VENV=false
CLEAN_ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            CLEAN_ALL=true
            shift
            ;;
        --db)
            CLEAN_DB=true
            shift
            ;;
        --venv)
            CLEAN_VENV=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--all] [--db] [--venv]"
            exit 1
            ;;
    esac
done

# 确认
if [ "$CLEAN_ALL" = true ] || [ "$CLEAN_DB" = true ] || [ "$CLEAN_VENV" = true ]; then
    echo "⚠  警告: 将清理数据库/虚拟环境，这可能会删除重要数据！"
    read -p "是否继续? (yes/no): " response
    if [ "$response" != "yes" ] && [ "$response" != "y" ]; then
        echo "已取消"
        exit 0
    fi
fi

TOTAL_COUNT=0

# 清理 Python 缓存
echo ""
echo "[1/6] 清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "dist" -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
echo "  ✓ Python 缓存已清理"

# 清理前端缓存
echo ""
echo "[2/6] 清理前端缓存..."
if [ -d "frontend" ]; then
    rm -rf frontend/dist 2>/dev/null || true
    rm -rf frontend/build 2>/dev/null || true
    rm -rf frontend/.vite 2>/dev/null || true
    rm -rf frontend/.cache 2>/dev/null || true
    rm -rf frontend/node_modules/.cache 2>/dev/null || true
    find frontend -name "*.tsbuildinfo" -delete 2>/dev/null || true
    find frontend -name ".eslintcache" -delete 2>/dev/null || true
    echo "  ✓ 前端缓存已清理"
else
    echo "  - frontend 目录不存在，跳过"
fi

# 清理日志
echo ""
echo "[3/6] 清理日志文件..."
find . -type f -name "*.log" -not -path "*/node_modules/*" -delete 2>/dev/null || true
find . -type f -name "*.log.*" -not -path "*/node_modules/*" -delete 2>/dev/null || true
echo "  ✓ 日志文件已清理"

# 清理操作系统缓存
echo ""
echo "[4/6] 清理操作系统缓存..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true
find . -name "desktop.ini" -delete 2>/dev/null || true
echo "  ✓ 操作系统缓存已清理"

# 清理 IDE 缓存
echo ""
echo "[5/6] 清理 IDE 缓存..."
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*.swo" -delete 2>/dev/null || true
echo "  ✓ IDE 缓存已清理"

# 清理数据库（可选）
if [ "$CLEAN_ALL" = true ] || [ "$CLEAN_DB" = true ]; then
    echo ""
    echo "[6/6] 清理数据库文件..."
    find . -type f -name "*.db" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    find . -type f -name "*.sqlite" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    find . -type f -name "*.sqlite3" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    echo "  ✓ 数据库文件已清理"
fi

# 清理虚拟环境（可选）
if [ "$CLEAN_ALL" = true ] || [ "$CLEAN_VENV" = true ]; then
    echo ""
    echo "[额外] 清理虚拟环境..."
    rm -rf .venv venv ENV env venv.bak env.bak 2>/dev/null || true
    rm -rf backend/.venv backend/venv 2>/dev/null || true
    echo "  ✓ 虚拟环境已清理"
fi

echo ""
echo "============================================================"
echo "清理完成！"
echo "============================================================"
echo ""
echo "提示: 下次运行前请重新安装依赖:"
echo "  - 后端: cd backend && pip install -e ."
echo "  - 前端: cd frontend && npm install"
