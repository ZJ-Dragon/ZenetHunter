@echo off
REM ============================================================
REM ZenetHunter 本地启动脚本 (Windows)
REM ============================================================
REM 功能：
REM   - 自动清理残留进程和端口
REM   - 清理 Python/前端/OS 缓存
REM   - 智能环境检测和依赖安装
REM   - 数据库检查和自动修复
REM   - 前后端一键启动
REM
REM 用法：
REM   start-local.bat              # 正常启动
REM   start-local.bat --clean      # 深度清理后启动（清理缓存）
REM   start-local.bat --clean-all  # 完全清理后启动（包括数据库和虚拟环境）
REM ============================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM 参数解析
set CLEAN_MODE=0
set CLEAN_ALL=0

:parse_args
if "%1"=="" goto args_done
if "%1"=="--clean" (
    set CLEAN_MODE=1
    shift
    goto parse_args
)
if "%1"=="--clean-all" (
    set CLEAN_MODE=1
    set CLEAN_ALL=1
    shift
    goto parse_args
)
if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help
echo 未知参数: %1
echo 使用 --help 查看帮助
exit /b 1

:show_help
echo 用法: %0 [选项]
echo.
echo 选项:
echo   --clean       启动前清理缓存（Python、前端、日志等）
echo   --clean-all   启动前完全清理（包括数据库和虚拟环境）
echo   -h, --help    显示此帮助信息
echo.
echo 示例:
echo   start-local.bat              # 正常启动
echo   start-local.bat --clean      # 清理缓存后启动
exit /b 0

:args_done

echo.
echo ============================================================
echo         ZenetHunter 本地启动脚本 v2.0 (Windows)
echo     集成：清理、检测、依赖、数据库、前后端启动
echo ============================================================
echo.

REM ============================================================
REM 步骤 1: 清理残留进程
REM ============================================================
echo === 步骤 1/6: 清理残留进程 ===

echo   清理 uvicorn 进程...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST 2^>nul ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"uvicorn" >nul && (
        taskkill /F /PID %%a >nul 2>&1
        echo     已终止进程 %%a
    )
)
echo   √ 后端进程清理完成

echo   清理 vite 进程...
taskkill /F /FI "WINDOWTITLE eq vite*" >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST 2^>nul ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"vite" >nul && (
        taskkill /F /PID %%a >nul 2>&1
        echo     已终止进程 %%a
    )
)
echo   √ 前端进程清理完成

REM 清理端口占用
echo   检查端口占用...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000.*LISTENING"') do (
    echo     端口 8000 被占用 (PID: %%a)，正在释放...
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173.*LISTENING"') do (
    echo     端口 5173 被占用 (PID: %%a)，正在释放...
    taskkill /F /PID %%a >nul 2>&1
)
echo   √ 端口清理完成
echo.

REM ============================================================
REM 步骤 2: 清理缓存（可选）
REM ============================================================
if %CLEAN_MODE%==1 goto clean_caches
echo === 步骤 2/6: 跳过缓存清理（使用 --clean 启用）===
echo.
goto check_python

:clean_caches
echo === 步骤 2/6: 清理缓存 ===

echo   清理 Python 缓存...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyo) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyd) do @if exist "%%f" del /q "%%f" 2>nul
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (.mypy_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (.ruff_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo   √ Python 缓存已清理

echo   清理前端缓存...
if exist "frontend" (
    if exist "frontend\dist" rd /s /q "frontend\dist" 2>nul
    if exist "frontend\.vite" rd /s /q "frontend\.vite" 2>nul
    if exist "frontend\.cache" rd /s /q "frontend\.cache" 2>nul
    if exist "frontend\node_modules\.cache" rd /s /q "frontend\node_modules\.cache" 2>nul
    for /r frontend %%f in (*.tsbuildinfo) do @if exist "%%f" del /q "%%f" 2>nul
    for /r frontend %%f in (.eslintcache) do @if exist "%%f" del /q "%%f" 2>nul
)
echo   √ 前端缓存已清理

echo   清理日志文件...
for /r . %%f in (*.log) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.log.*) do @if exist "%%f" del /q "%%f" 2>nul
echo   √ 日志文件已清理

echo   清理系统缓存...
for /r . %%f in (Thumbs.db) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (desktop.ini) do @if exist "%%f" del /q "%%f" 2>nul
echo   √ 系统缓存已清理

echo   清理 IDE 缓存...
for /r . %%f in (*.swp) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.swo) do @if exist "%%f" del /q "%%f" 2>nul
echo   √ IDE 缓存已清理

echo   清理数据库锁文件...
if exist "backend\data\zenethunter.db-shm" del /q "backend\data\zenethunter.db-shm" 2>nul
if exist "backend\data\zenethunter.db-wal" del /q "backend\data\zenethunter.db-wal" 2>nul
echo   √ 数据库锁文件已清理

if %CLEAN_ALL%==0 goto check_python

echo.
echo ⚠ 警告: 将清理数据库和虚拟环境！
set /p confirm="确认继续? (yes/no): "
if /i not "%confirm%"=="yes" if /i not "%confirm%"=="y" (
    echo 已取消深度清理
    goto check_python
)

echo   清理数据库文件...
for /r . %%f in (*.db) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.sqlite) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.sqlite3) do @if exist "%%f" del /q "%%f" 2>nul
echo   √ 数据库文件已清理

echo   清理虚拟环境...
if exist ".venv" rd /s /q ".venv" 2>nul
if exist "venv" rd /s /q "venv" 2>nul
if exist "backend\.venv" rd /s /q "backend\.venv" 2>nul
if exist "backend\venv" rd /s /q "backend\venv" 2>nul
echo   √ 虚拟环境已清理
echo.

REM ============================================================
REM 步骤 3: 检查 Python 环境
REM ============================================================
:check_python
echo === 步骤 3/6: 检查 Python 环境 ===

python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 错误: 未找到 Python
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo   √ %PYTHON_VERSION%

cd backend

REM 检查/创建虚拟环境
if not exist ".venv" (
    echo   创建虚拟环境...
    python -m venv .venv
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat
echo   √ 虚拟环境已激活
echo.

REM ============================================================
REM 步骤 4: 安装依赖
REM ============================================================
echo === 步骤 4/6: 安装/更新依赖 ===

python -m pip install -q --upgrade pip
python -m pip install -q -e . || (
    echo   警告: editable 安装失败，尝试直接安装依赖...
    python -m pip install -q greenlet>=3.0.0
    python -m pip install -q -e .
)
echo   √ 依赖安装完成
echo.

REM ============================================================
REM 步骤 5: 检查数据库
REM ============================================================
echo === 步骤 5/6: 检查数据库 ===

if "%DATABASE_URL%"=="" (
    set DATABASE_URL=sqlite+aiosqlite:///./data/zenethunter.db
    echo   √ 使用默认 SQLite 数据库
)

if not exist "data" mkdir data

if exist "data\zenethunter.db" (
    echo   √ 数据库已存在
) else (
    echo   √ 将在首次启动时创建数据库
)
echo.

REM ============================================================
REM 步骤 6: 启动服务
REM ============================================================
echo === 步骤 6/6: 启动服务 ===

REM 设置环境变量
set APP_ENV=development
set APP_HOST=0.0.0.0
set APP_PORT=8000
set LOG_LEVEL=info
set CORS_ALLOW_ORIGINS=null,http://localhost:8000,http://localhost:5173,http://127.0.0.1:5173

REM 检测管理员权限
set IS_ADMIN=0
net session >nul 2>&1
if %errorlevel%==0 (
    set IS_ADMIN=1
    echo   √ 检测到管理员权限，将启用所有网络功能
) else (
    echo   ⚠ 当前未使用管理员权限，某些功能可能受限
    echo     提示: 右键点击，选择"以管理员身份运行"
)

REM 获取本地 IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    set LOCAL_IP=!LOCAL_IP:~1!
    goto :found_ip
)
:found_ip
if defined LOCAL_IP (
    set CORS_ALLOW_ORIGINS=%CORS_ALLOW_ORIGINS%,http://%LOCAL_IP%:5173
)

REM 启动前端
cd /d "%~dp0"
if exist "frontend" (
    cd frontend
    if not exist "node_modules" (
        echo   安装前端依赖...
        call npm install
    )
    echo   启动 React 前端服务器...
    start /B npm run dev >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo   √ 前端服务器已启动 (端口: 5173)
    cd /d "%~dp0"
) else (
    echo   ⚠ 未找到 frontend 目录，跳过前端启动
)

echo.
echo ============================================================
echo                    服务启动完成
echo ============================================================
echo   后端 API:  http://localhost:8000
echo   API 文档:  http://localhost:8000/docs
echo   前端页面:  http://localhost:5173
if defined LOCAL_IP (
echo   网络访问:  http://%LOCAL_IP%:5173
)
echo ============================================================
echo   按 Ctrl+C 关闭所有服务
echo ============================================================
echo.

REM 启动后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

REM 清理：停止前端服务器（当后端停止时）
cd /d "%~dp0"
taskkill /F /FI "WINDOWTITLE eq vite*" >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST 2^>nul ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"vite" >nul && taskkill /F /PID %%a >nul 2>&1
)

pause
