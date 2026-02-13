@echo off
REM ============================================================
REM ZenetHunter local startup script (Windows)
REM ============================================================
REM Features:
REM   - Kill leftover processes/ports
REM   - Clear caches/logs (optional deep clean)
REM   - Detect Python venv and install backend deps
REM   - Quick DB sanity check and runtime reset
REM   - Launch backend (uvicorn) and frontend (Vite)
REM
REM Usage:
REM   start-local.bat              # normal start
REM   start-local.bat --clean      # clear caches before start
REM   start-local.bat --clean-all  # deep clean (caches + DB + venv)
REM ============================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ------------------------------------------------------------
REM Args
REM ------------------------------------------------------------
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
echo Unknown option: %1
echo Use --help for usage
exit /b 1

:show_help
echo Usage: %0 [options]
echo.
echo Options:
echo   --clean       Clear caches before start
echo   --clean-all   Deep clean (caches + DB + virtualenv)
echo   -h, --help    Show this help
exit /b 0

:args_done

echo.
echo ============================================================
echo         ZenetHunter local starter v2.0 (Windows)
echo     Cleanup ^| Checks ^| Deps ^| DB ^| Frontend ^| Backend
echo ============================================================
echo.

REM ------------------------------------------------------------
REM Step 1: cleanup
REM ------------------------------------------------------------
echo === Step 1/6: Clean leftover processes ===

echo   Killing uvicorn processes...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST 2^>nul ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"uvicorn" >nul && (
        taskkill /F /PID %%a >nul 2>&1
        echo     terminated %%a
    )
)
echo   √ Backend processes cleared

echo   Killing vite processes...
taskkill /F /FI "WINDOWTITLE eq vite*" >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST 2^>nul ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"vite" >nul && (
        taskkill /F /PID %%a >nul 2>&1
        echo     terminated %%a
    )
)
echo   √ Frontend processes cleared

echo   Checking ports...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000.*LISTENING"') do (
    echo     Port 8000 in use (PID: %%a), freeing...
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173.*LISTENING"') do (
    echo     Port 5173 in use (PID: %%a), freeing...
    taskkill /F /PID %%a >nul 2>&1
)
echo   √ Ports cleared
echo.

REM ------------------------------------------------------------
REM Step 2: caches
REM ------------------------------------------------------------
if %CLEAN_MODE%==1 goto clean_caches
echo === Step 2/6: Skip cache clean (use --clean to enable) ===
echo.
goto check_python

:clean_caches
echo === Step 2/6: Clear caches ===

echo   Python caches...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyo) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyd) do @if exist "%%f" del /q "%%f" 2>nul
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (.mypy_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (.ruff_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo   √ Python caches cleared

echo   Frontend caches...
if exist "frontend" (
    if exist "frontend\dist" rd /s /q "frontend\dist" 2>nul
    if exist "frontend\.vite" rd /s /q "frontend\.vite" 2>nul
    if exist "frontend\.cache" rd /s /q "frontend\.cache" 2>nul
    if exist "frontend\node_modules\.cache" rd /s /q "frontend\node_modules\.cache" 2>nul
    for /r frontend %%f in (*.tsbuildinfo) do @if exist "%%f" del /q "%%f" 2>nul
    for /r frontend %%f in (.eslintcache) do @if exist "%%f" del /q "%%f" 2>nul
)
echo   √ Frontend caches cleared

echo   Log files...
for /r . %%f in (*.log) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.log.*) do @if exist "%%f" del /q "%%f" 2>nul
echo   √ Logs removed

echo   OS junk...
for /r . %%f in (Thumbs.db) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (desktop.ini) do @if exist "%%f" del /q "%%f" 2>nul
echo   √ OS junk removed

echo   IDE swap...
for /r . %%f in (*.swp) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.swo) do @if exist "%%f" del /q "%%f" 2>nul
echo   √ IDE swap removed

echo   DB lock files...
if exist "backend\data\zenethunter.db-shm" del /q "backend\data\zenethunter.db-shm" 2>nul
if exist "backend\data\zenethunter.db-wal" del /q "backend\data\zenethunter.db-wal" 2>nul
echo   √ DB lock files cleared

if %CLEAN_ALL%==0 goto check_python

echo.
echo ⚠ Warning: DB and virtualenv will be removed!
set /p confirm="Continue? (yes/no): "
if /i not "%confirm%"=="yes" if /i not "%confirm%"=="y" (
    echo Deep clean cancelled
    goto check_python
)

echo   Removing database files...
for /r . %%f in (*.db) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.sqlite) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.sqlite3) do @if exist "%%f" del /q "%%f" 2>nul
echo   √ Database files removed

echo   Removing virtualenv...
if exist ".venv" rd /s /q ".venv" 2>nul
if exist "venv" rd /s /q "venv" 2>nul
if exist "backend\.venv" rd /s /q "backend\.venv" 2>nul
if exist "backend\venv" rd /s /q "backend\venv" 2>nul
echo   √ Virtualenv removed
echo.

REM ------------------------------------------------------------
REM Step 3: Python env
REM ------------------------------------------------------------
:check_python
echo === Step 3/6: Check Python ===

python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Error: python not found
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo   √ %PYTHON_VERSION%

cd backend

if not exist ".venv" (
    echo   Creating virtualenv...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
echo   √ Virtualenv activated
echo.

REM ------------------------------------------------------------
REM Step 4: deps
REM ------------------------------------------------------------
echo === Step 4/6: Install/update backend deps ===

python -m pip install -q --upgrade pip
python -m pip install -q -e . || (
    echo   Warning: editable install failed, trying fallback...
    python -m pip install -q greenlet>=3.0.0
    python -m pip install -q -e .
)
echo   √ Dependencies installed
echo.

REM ------------------------------------------------------------
REM Step 5: DB check
REM ------------------------------------------------------------
echo === Step 5/6: Database check ===

if "%DATABASE_URL%"=="" (
    set DATABASE_URL=sqlite+aiosqlite:///./data/zenethunter.db
    echo   √ Using default SQLite database
)

if not exist "data" mkdir data

if exist "data\zenethunter.db" (
    echo   √ Database exists
) else (
    echo   √ Database will be created on first run
)
echo.

REM ------------------------------------------------------------
REM Step 5.5: reset runtime
REM ------------------------------------------------------------
echo === Step 5.5/6: Reset volatile runtime data (keep manual library) ===
if "%APP_ENV%"=="" set APP_ENV=development
python -m app.maintenance.reset_runtime_data
if errorlevel 1 (
    echo ✗ Runtime reset failed (allowed only for APP_ENV=development)
    exit /b 1
)
echo   √ Runtime tables cleared (manual library kept)
echo.

REM ------------------------------------------------------------
REM Step 6: start services
REM ------------------------------------------------------------
echo === Step 6/6: Start services ===

set APP_ENV=development
set APP_HOST=0.0.0.0
set APP_PORT=8000
set LOG_LEVEL=info
set CORS_ALLOW_ORIGINS=null,http://localhost:8000,http://localhost:5173,http://127.0.0.1:5173

set IS_ADMIN=0
net session >nul 2>&1
if %errorlevel%==0 (
    set IS_ADMIN=1
    echo   √ Admin privileges detected: full network features enabled
) else (
    echo   ⚠ Not running as admin; some probes may be limited
    echo     Tip: right-click and "Run as administrator"
)

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    set LOCAL_IP=!LOCAL_IP:~1!
    goto :found_ip
)
:found_ip
if defined LOCAL_IP (
    set CORS_ALLOW_ORIGINS=%CORS_ALLOW_ORIGINS%,http://%LOCAL_IP%:5173
)

cd /d "%~dp0"
if exist "frontend" (
    cd frontend
    if not exist "node_modules" (
        echo   Installing frontend dependencies...
        call npm install
    )
    echo   Starting React dev server...
    start /B npm run dev >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo   √ Frontend started (port: 5173)
    cd /d "%~dp0"
) else (
    echo   ⚠ frontend directory not found; skipping frontend start
)

echo.
echo ============================================================
echo                    Services are up
echo ============================================================
echo   Backend API:  http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo   Frontend:     http://localhost:5173
if defined LOCAL_IP (
echo   LAN access:   http://%LOCAL_IP%:5173
)
echo ============================================================
echo   Press Ctrl+C to stop all services
echo ============================================================
echo.

cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

cd /d "%~dp0"
taskkill /F /FI "WINDOWTITLE eq vite*" >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST 2^>nul ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"vite" >nul && taskkill /F /PID %%a >nul 2>&1
)

pause
