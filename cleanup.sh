#!/bin/bash
# ZenetHunter 清理脚本 - 清理所有残留进程和端口

echo "=== ZenetHunter 清理脚本 ==="
echo ""

# 清理uvicorn进程
echo "1. 清理 uvicorn 进程..."
UVICORN_PIDS=$(ps aux | grep -E "uvicorn app.main|python.*app.main" | grep -v grep | awk '{print $2}')

if [ ! -z "$UVICORN_PIDS" ]; then
    echo "发现进程:"
    ps aux | grep -E "uvicorn app.main|python.*app.main" | grep -v grep
    echo ""
    echo "正在终止..."
    
    for pid in $UVICORN_PIDS; do
        kill -KILL $pid 2>/dev/null || sudo kill -KILL $pid 2>/dev/null || true
    done
    
    sleep 2
    echo "✅ uvicorn 进程已清理"
else
    echo "✅ 无 uvicorn 进程"
fi

# 清理vite进程
echo ""
echo "2. 清理 vite 进程..."
VITE_PIDS=$(ps aux | grep -E "vite.*ZenetHunter|node.*vite" | grep -v grep | awk '{print $2}')

if [ ! -z "$VITE_PIDS" ]; then
    for pid in $VITE_PIDS; do
        kill -KILL $pid 2>/dev/null || true
    done
    echo "✅ vite 进程已清理"
else
    echo "✅ 无 vite 进程"
fi

# 清理端口8000
echo ""
echo "3. 清理端口 8000..."
PORT_8000=$(lsof -ti:8000 2>/dev/null)

if [ ! -z "$PORT_8000" ]; then
    echo "端口8000被占用 (PID: $PORT_8000)"
    kill -KILL $PORT_8000 2>/dev/null || sudo kill -KILL $PORT_8000 2>/dev/null || true
    sleep 1
    echo "✅ 端口 8000 已释放"
else
    echo "✅ 端口 8000 空闲"
fi

# 清理端口5173
echo ""
echo "4. 清理端口 5173..."
PORT_5173=$(lsof -ti:5173 2>/dev/null)

if [ ! -z "$PORT_5173" ]; then
    echo "端口5173被占用 (PID: $PORT_5173)"
    kill -KILL $PORT_5173 2>/dev/null || true
    sleep 1
    echo "✅ 端口 5173 已释放"
else
    echo "✅ 端口 5173 空闲"
fi

# 清理数据库锁（可选）
echo ""
echo "5. 清理数据库锁文件（如果存在）..."
if [ -f "backend/data/zenethunter.db-shm" ] || [ -f "backend/data/zenethunter.db-wal" ]; then
    rm -f backend/data/zenethunter.db-shm backend/data/zenethunter.db-wal
    echo "✅ 数据库锁文件已清理"
else
    echo "✅ 无数据库锁文件"
fi

echo ""
echo "=== 清理完成 ==="
echo ""
echo "现在可以运行: ./start-local.sh"
