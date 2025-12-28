@echo off
REM 本地启动脚本 - Windows 版本

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === ZenetHunter 本地启动 ===
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    pause
    exit /b 1
)

REM 进入后端目录
cd backend

REM 检查虚拟环境
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 安装依赖
echo 安装/更新依赖...
python -m pip install -q --upgrade pip
REM 确保安装所有必需依赖，包括 greenlet（SQLAlchemy 异步必需）
python -m pip install -q -e . || (
    echo 警告: 使用 pip install -e . 失败，尝试直接安装依赖...
    python -m pip install -q greenlet>=3.0.0
    python -m pip install -q -e .
)

REM 设置环境变量
set APP_ENV=development
set APP_HOST=0.0.0.0
set APP_PORT=8000
set LOG_LEVEL=info
REM CORS: 允许 React 前端（Vite 开发服务器端口 5173）和 localhost:8000（后端）
set CORS_ALLOW_ORIGINS=null,http://localhost:8000,http://localhost:5173,http://127.0.0.1:5173

if "%DATABASE_URL%"=="" (
    echo 使用默认 SQLite 数据库
    set DATABASE_URL=sqlite+aiosqlite:///./data/zenethunter.db
)

REM 检测操作系统
echo.
echo 检测到操作系统: Windows
echo ✓ Windows 检测到，使用 Windows 优化配置
echo 提示: 某些网络功能可能需要管理员权限
echo 提示: 如需管理员权限运行，请右键点击命令提示符，选择"以管理员身份运行"
echo.

REM 获取本地 IP 地址
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    set LOCAL_IP=!LOCAL_IP:~1!
    goto :found_ip
)
:found_ip

REM 如果检测到本地 IP，也添加到 CORS 允许列表
if defined LOCAL_IP (
    set CORS_ALLOW_ORIGINS=%CORS_ALLOW_ORIGINS%,http://%LOCAL_IP%:5173
)

echo.
echo 启动服务...
echo 后端 API: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 前端页面 (React):
echo   - 本地访问: http://localhost:5173
if defined LOCAL_IP (
    echo   - 网络访问: http://%LOCAL_IP%:5173
)
echo.
echo 提示: React 前端服务器将在后台运行（Vite 开发服务器）
echo 提示: CORS 已配置，允许从前端服务器访问后端 API
echo 按 Ctrl+C 停止所有服务
echo.

REM 启动前端服务器（React + Vite，后台运行）
cd /d "%~dp0"
if exist "frontend" (
    cd frontend

    REM 检查是否已安装依赖
    if not exist "node_modules" (
        echo 安装前端依赖...
        call npm install
    )

    REM 启动 Vite 开发服务器（后台运行）
    echo 启动 React 前端服务器...
    start /B npm run dev >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo React 前端服务器已启动 (端口: 5173)

    cd /d "%~dp0"
) else (
    echo 警告: frontend 目录不存在，跳过前端服务器启动
    echo 提示: 请安装 Node.js (https://nodejs.org/) 以使用 React 前端
)

REM 启动后端（前台运行）
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

REM 清理：停止前端服务器（如果后端停止）
cd /d "%~dp0"
REM 停止 Vite 进程
taskkill /F /FI "WINDOWTITLE eq vite*" >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"vite" >nul && taskkill /F /PID %%a >nul 2>&1
)

pause
