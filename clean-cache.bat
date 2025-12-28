@echo off
REM ZenetHunter 缓存清理脚本 (Windows)

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo ZenetHunter 缓存清理工具 (Windows 版本)
echo ============================================================
echo 项目目录: %CD%
echo.

REM 检查参数
set CLEAN_DB=0
set CLEAN_VENV=0
set CLEAN_ALL=0

:parse_args
if "%1"=="" goto args_done
if "%1"=="--all" set CLEAN_ALL=1
if "%1"=="--db" set CLEAN_DB=1
if "%1"=="--venv" set CLEAN_VENV=1
shift
goto parse_args

:args_done

REM 确认
if %CLEAN_ALL%==1 goto confirm
if %CLEAN_DB%==1 goto confirm
if %CLEAN_VENV%==1 goto confirm
goto start_clean

:confirm
echo ⚠  警告: 将清理数据库/虚拟环境，这可能会删除重要数据！
set /p response="是否继续? (yes/no): "
if /i not "%response%"=="yes" if /i not "%response%"=="y" (
    echo 已取消
    exit /b 0
)

:start_clean

REM 清理 Python 缓存
echo.
echo [1/6] 清理 Python 缓存...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyo) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyd) do @if exist "%%f" del /q "%%f" 2>nul
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (.mypy_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (.ruff_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (build) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (dist) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo   ✓ Python 缓存已清理

REM 清理前端缓存
echo.
echo [2/6] 清理前端缓存...
if exist "frontend" (
    if exist "frontend\dist" rd /s /q "frontend\dist" 2>nul
    if exist "frontend\build" rd /s /q "frontend\build" 2>nul
    if exist "frontend\.vite" rd /s /q "frontend\.vite" 2>nul
    if exist "frontend\.cache" rd /s /q "frontend\.cache" 2>nul
    if exist "frontend\node_modules\.cache" rd /s /q "frontend\node_modules\.cache" 2>nul
    for /r frontend %%f in (*.tsbuildinfo) do @if exist "%%f" del /q "%%f" 2>nul
    for /r frontend %%f in (.eslintcache) do @if exist "%%f" del /q "%%f" 2>nul
    echo   ✓ 前端缓存已清理
) else (
    echo   - frontend 目录不存在，跳过
)

REM 清理日志
echo.
echo [3/6] 清理日志文件...
for /r . %%f in (*.log) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.log.*) do @if exist "%%f" del /q "%%f" 2>nul
echo   ✓ 日志文件已清理

REM 清理操作系统缓存
echo.
echo [4/6] 清理操作系统缓存...
for /r . %%f in (Thumbs.db) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (desktop.ini) do @if exist "%%f" del /q "%%f" 2>nul
echo   ✓ 操作系统缓存已清理

REM 清理 IDE 缓存
echo.
echo [5/6] 清理 IDE 缓存...
for /r . %%f in (*.swp) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.swo) do @if exist "%%f" del /q "%%f" 2>nul
echo   ✓ IDE 缓存已清理

REM 清理数据库（可选）
if %CLEAN_ALL%==1 goto clean_db
if %CLEAN_DB%==1 goto clean_db
goto check_venv

:clean_db
echo.
echo [6/6] 清理数据库文件...
for /r . %%f in (*.db) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.sqlite) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.sqlite3) do @if exist "%%f" del /q "%%f" 2>nul
echo   ✓ 数据库文件已清理

:check_venv
REM 清理虚拟环境（可选）
if %CLEAN_ALL%==1 goto clean_venv
if %CLEAN_VENV%==1 goto clean_venv
goto done

:clean_venv
echo.
echo [额外] 清理虚拟环境...
if exist ".venv" rd /s /q ".venv" 2>nul
if exist "venv" rd /s /q "venv" 2>nul
if exist "ENV" rd /s /q "ENV" 2>nul
if exist "env" rd /s /q "env" 2>nul
if exist "backend\.venv" rd /s /q "backend\.venv" 2>nul
if exist "backend\venv" rd /s /q "backend\venv" 2>nul
echo   ✓ 虚拟环境已清理

:done
echo.
echo ============================================================
echo 清理完成！
echo ============================================================
echo.
echo 提示: 下次运行前请重新安装依赖:
echo   - 后端: cd backend ^&^& pip install -e .
echo   - 前端: cd frontend ^&^& npm install
echo.

pause
