#!/bin/bash
# ============================================================
# ZenetHunter local bootstrap script (Linux/macOS)
# ============================================================
# Features:
#   - Kill leftover backend/frontend processes and free ports
#   - Clear caches/logs (optional deep clean)
#   - Detect Python/virtualenv and install backend deps
#   - Quick DB sanity check and runtime reset
#   - Launch backend (uvicorn) and frontend (Vite)
#
# Usage:
#   ./start-local.sh              # normal start
#   ./start-local.sh --clean      # clear caches before start
#   ./start-local.sh --clean-all  # deep clean (including DB and venv)
#   sudo ./start-local.sh         # recommended for full network features
# ============================================================

# Intentionally not using `set -e` to avoid exiting on non-critical warnings

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================================
# Args
# ============================================================
CLEAN_MODE=false
CLEAN_ALL=false
SCRIPT_ARGS=("$@")

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
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --clean       Clear caches before start"
            echo "  --clean-all   Deep clean (caches + DB + virtualenv)"
            echo "  -h, --help    Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage"
            exit 1
            ;;
    esac
done

# ============================================================
# Colors
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() { echo -e "${BLUE}=== $1 ===${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

PYTHON_BIN=""

# ============================================================
# Process cleanup
# ============================================================
cleanup_old_processes() {
    print_header "Cleaning leftover processes"

    local uvicorn_pids
    uvicorn_pids=$(ps aux | grep -E "uvicorn app.main|python.*app.main" | grep -v grep | awk '{print $2}')
    if [ -n "$uvicorn_pids" ]; then
        print_warning "Found stale backend processes"
        for pid in $uvicorn_pids; do
            kill -KILL "$pid" 2>/dev/null || true
        done
        sleep 1
        print_success "Backend processes cleared"
    else
        print_success "No stale backend processes"
    fi

    local vite_pids
    vite_pids=$(ps aux | grep -E "vite.*ZenetHunter|node.*vite" | grep -v grep | awk '{print $2}')
    if [ -n "$vite_pids" ]; then
        print_warning "Found stale frontend processes"
        for pid in $vite_pids; do
            kill -KILL "$pid" 2>/dev/null || true
        done
        sleep 1
        print_success "Frontend processes cleared"
    else
        print_success "No stale frontend processes"
    fi
}

# ============================================================
# Port cleanup
# ============================================================
check_and_free_port() {
    local port=$1
    local name=$2

    if command -v lsof &> /dev/null; then
        local pids
        pids=$(lsof -ti:"$port" 2>/dev/null)
        if [ -n "$pids" ]; then
            print_warning "$name port $port is in use (PID: $pids)"
            kill -KILL $pids 2>/dev/null || true
            sleep 1
            print_success "Port $port freed"
            return 0
        fi
    fi

    if ! python3 - <<PY 2>/dev/null
import socket
s=socket.socket()
s.bind(('', $port))
s.close()
PY
    then
        print_warning "$name port $port may be in use"
        sleep 1
    fi

    print_success "Port $port is available"
    return 0
}

# ============================================================
# Cache cleanup
# ============================================================
clean_caches() {
    print_header "Clearing caches"

    echo "  Python caches..."
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
    print_success "Python caches cleared"

    if [ -d "frontend" ]; then
        echo "  Frontend caches..."
        rm -rf frontend/dist frontend/.vite frontend/.cache frontend/node_modules/.cache 2>/dev/null || true
        find frontend -name "*.tsbuildinfo" -delete 2>/dev/null || true
        find frontend -name ".eslintcache" -delete 2>/dev/null || true
        print_success "Frontend caches cleared"
    fi

    echo "  Log files..."
    find . -type f -name "*.log" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    find . -type f -name "*.log.*" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    rm -f /tmp/zenethunter-*.log 2>/dev/null || true
    print_success "Logs removed"

    echo "  OS junk..."
    find . -name ".DS_Store" -delete 2>/dev/null || true
    find . -name "Thumbs.db" -delete 2>/dev/null || true
    find . -name "desktop.ini" -delete 2>/dev/null || true
    print_success "OS junk removed"

    echo "  IDE swap..."
    find . -type f -name "*.swp" -delete 2>/dev/null || true
    find . -type f -name "*.swo" -delete 2>/dev/null || true
    print_success "IDE swap removed"

    echo "  Database lock files..."
    rm -f backend/data/zenethunter.db-shm backend/data/zenethunter.db-wal 2>/dev/null || true
    print_success "DB lock files cleared"
}

# ============================================================
# Deep clean
# ============================================================
clean_all() {
    clean_caches

    print_header "Deep clean (DB + virtualenv)"

    echo -e "${YELLOW}⚠ Warning: DB and virtualenv will be removed!${NC}"
    read -p "Continue? (yes/no): " response
    if [ "$response" != "yes" ] && [ "$response" != "y" ]; then
        echo "Deep clean cancelled"
        return
    fi

    echo "  Removing database files..."
    find . -type f -name "*.db" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    find . -type f -name "*.sqlite" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    find . -type f -name "*.sqlite3" -not -path "*/node_modules/*" -delete 2>/dev/null || true
    print_success "Database files removed"

    echo "  Removing virtualenv..."
    rm -rf .venv venv ENV env venv.bak env.bak 2>/dev/null || true
    rm -rf backend/.venv backend/venv 2>/dev/null || true
    print_success "Virtualenv removed"
}

quote_args() {
    python3 - "$@" <<'PY'
import shlex
import sys
print(" ".join(shlex.quote(arg) for arg in sys.argv[1:]))
PY
}

maybe_request_macos_admin() {
    if [ "$(uname -s)" != "Darwin" ]; then
        return
    fi

    if [ "${EUID:-$(id -u)}" -eq 0 ]; then
        return
    fi

    if [ "${ZENETHUNTER_ELEVATED_RELAUNCH:-0}" = "1" ]; then
        return
    fi

    echo ""
    print_warning "Raw packet features and active defense need administrator privileges on macOS."
    read -p "Open the macOS authorization dialog and relaunch elevated? (Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_warning "Continuing without elevation"
        return
    fi

    if ! command -v osascript >/dev/null 2>&1; then
        print_warning "osascript not found; cannot open macOS authorization dialog"
        return
    fi

    local quoted_script quoted_args command_text apple_script
    quoted_script=$(quote_args "$SCRIPT_DIR/start-local.sh")
    quoted_args=$(quote_args "${SCRIPT_ARGS[@]}")
    command_text="cd $(quote_args "$SCRIPT_DIR") && ZENETHUNTER_ELEVATED_RELAUNCH=1 ${quoted_script}"
    if [ -n "$quoted_args" ]; then
        command_text="${command_text} ${quoted_args}"
    fi
    apple_script=$(python3 - "$command_text" <<'PY'
import sys

command = sys.argv[1].replace("\\", "\\\\").replace('"', '\\"')
print(f'do shell script "{command}" with administrator privileges')
PY
)

    if osascript -e "$apple_script"; then
        print_success "Elevated launcher started"
        exit 0
    fi

    print_warning "Administrator authorization was cancelled or failed"
}

select_python_runtime() {
    if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
        print_success "Conda env detected: $CONDA_DEFAULT_ENV"
        PYTHON_BIN="$(command -v python)"
        return
    fi

    if [ -n "$VIRTUAL_ENV" ]; then
        print_success "Virtualenv detected: $VIRTUAL_ENV"
        PYTHON_BIN="$(command -v python)"
        return
    fi

    if [ -d ".venv" ]; then
        echo "Activating local virtualenv..."
        # shellcheck disable=SC1091
        source .venv/bin/activate
        print_success "Activated .venv"
        PYTHON_BIN="$(command -v python)"
        return
    fi

    print_warning "No virtualenv detected"
    echo ""
    echo "Recommended:"
    echo "  1) conda activate <env-name>"
    echo "  2) python3 -m venv backend/.venv && source backend/.venv/bin/activate"
    echo ""
    read -p "Create backend/.venv automatically? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        python3 -m venv .venv
        # shellcheck disable=SC1091
        source .venv/bin/activate
        print_success "Created and activated backend/.venv"
        PYTHON_BIN="$(command -v python)"
        return
    fi

    read -p "Continue in the current system environment? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 1
    fi
    PYTHON_BIN="$(command -v python3)"
    print_warning "Using system interpreter: $PYTHON_BIN"
}

# ============================================================
# Graceful shutdown
# ============================================================
shutdown_handler() {
    echo ""
    print_header "Stopping services"

    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
        for _ in {1..6}; do
            if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
                print_success "Backend stopped gracefully"
                break
            fi
            sleep 0.5
        done
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            print_warning "Backend did not stop, forcing kill..."
            kill -KILL "$BACKEND_PID" 2>/dev/null || true
        fi
    fi

    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
        sleep 1
        kill -KILL "$FRONTEND_PID" 2>/dev/null || true
        print_success "Frontend stopped"
    fi

    pkill -f "uvicorn app.main" 2>/dev/null || true
    pkill -f "vite.*ZenetHunter" 2>/dev/null || true

    print_success "Cleanup complete"
    exit 0
}

trap shutdown_handler SIGINT SIGTERM EXIT

# ============================================================
# Banner
# ============================================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           ZenetHunter local starter v2.0               ║${NC}"
echo -e "${BLUE}║   Cleanup · Checks · Deps · DB · Frontend · Backend    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
# Step 1: cleanup
# ============================================================
print_header "Step 1/6: Cleanup stale resources"
cleanup_old_processes
check_and_free_port 8000 "Backend"
check_and_free_port 5173 "Frontend"
maybe_request_macos_admin

# ============================================================
# Step 2: caches
# ============================================================
if [ "$CLEAN_MODE" = true ]; then
    print_header "Step 2/6: Clear caches"
    if [ "$CLEAN_ALL" = true ]; then
        clean_all
    else
        clean_caches
    fi
else
    print_header "Step 2/6: Skip cache clean (use --clean to enable)"
fi

# ============================================================
# Step 3: Python env
# ============================================================
print_header "Step 3/6: Check Python"

if ! command -v python3 &> /dev/null; then
    print_error "python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
print_success "Python: $PYTHON_VERSION"

cd backend
select_python_runtime
print_success "Runtime interpreter: $PYTHON_BIN"

# ============================================================
# Step 4: deps
# ============================================================
print_header "Step 4/6: Install/update backend deps"

"$PYTHON_BIN" -m pip install -q --upgrade pip

if "$PYTHON_BIN" -m pip install -q -e . 2>/dev/null; then
    print_success "Backend deps installed (editable)"
else
    print_warning "Editable install failed, trying fallback..."
    "$PYTHON_BIN" -m pip install -q "greenlet>=3.0.0" "alembic>=1.13.0"
    "$PYTHON_BIN" -m pip install -q -e .
    print_success "Backend deps installed (fallback)"
fi

print_header "Step 4.5/6: Runtime support check"
if ! "$PYTHON_BIN" scripts/check_runtime.py --strict; then
    print_error "Runtime dependency check failed"
    print_warning "The interpreter above is not ready for the backend."
    print_warning "If you use conda and venv interchangeably, restart with the intended environment activated."
    exit 1
fi
print_success "Runtime support check passed"

# ============================================================
# Step 5: DB check
# ============================================================
print_header "Step 5/6: Database check"

export APP_ENV=${APP_ENV:-development}

if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="sqlite+aiosqlite:///./data/zenethunter.db"
    print_success "Using default SQLite database"
else
    print_success "Using DATABASE_URL from environment"
fi

mkdir -p data

if [ -f "data/zenethunter.db" ]; then
    COLUMN_CHECK=$(sqlite3 data/zenethunter.db "PRAGMA table_info(devices);" 2>/dev/null | grep "active_defense_status" || echo "")
    if [ -z "$COLUMN_CHECK" ]; then
        print_warning "Database schema mismatch, applying lightweight fix..."
        sqlite3 data/zenethunter.db <<EOF 2>/dev/null || true
ALTER TABLE devices ADD COLUMN active_defense_status TEXT DEFAULT 'idle';
ALTER TABLE devices ADD COLUMN recognition_manual_override INTEGER DEFAULT 0;
ALTER TABLE devices ADD COLUMN discovery_source TEXT DEFAULT NULL;
ALTER TABLE devices ADD COLUMN freshness_score INTEGER DEFAULT NULL;
UPDATE devices SET active_defense_status = COALESCE(attack_status, 'idle') WHERE active_defense_status IS NULL OR active_defense_status = '';
EOF
        print_success "Schema patched"
    else
        print_success "Database schema looks good"
    fi
else
    print_success "Database will be created on first run"
fi

# ============================================================
# Step 5.5: reset runtime (keep manual library)
# ============================================================
print_header "Step 5.5/6: Reset volatile runtime data"
if ! "$PYTHON_BIN" -m app.maintenance.reset_runtime_data; then
    print_error "Runtime reset failed (allowed only for APP_ENV=development)"
    exit 1
fi
print_success "Volatile tables cleared (manual library kept)"

# ============================================================
# Step 6: start services
# ============================================================
print_header "Step 6/6: Start services"

OS_TYPE=$(uname -s)
if [ "$EUID" -eq 0 ] || [ "$(id -u)" -eq 0 ]; then
    print_success "Running as root: full network features enabled"
else
    print_warning "Not running as root; some probes may be limited. Hint: sudo ./start-local.sh"
fi

export APP_ENV=development
export APP_HOST=0.0.0.0
export APP_PORT=8000
export LOG_LEVEL=info
export CORS_ALLOW_ORIGINS="null,http://localhost:8000,http://localhost:5173,http://127.0.0.1:5173"

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

cd "$SCRIPT_DIR"
FRONTEND_PID=""

if command -v node &> /dev/null && command -v npm &> /dev/null; then
    if [ -d "frontend" ]; then
        cd frontend
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi
        echo "Starting React dev server..."
        npm run dev > /tmp/zenethunter-frontend.log 2>&1 &
        FRONTEND_PID=$!
        sleep 2
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            print_success "Frontend started (PID: $FRONTEND_PID, port: 5173)"
        else
            print_warning "Frontend failed; see /tmp/zenethunter-frontend.log"
            FRONTEND_PID=""
        fi
        cd "$SCRIPT_DIR"
    fi
else
    print_warning "Node.js/npm not found; skipping frontend"
fi

cd backend

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   Services are up                      ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Backend API: http://localhost:8000                    ║${NC}"
echo -e "${GREEN}║  API Docs:    http://localhost:8000/docs               ║${NC}"
echo -e "${GREEN}║  Frontend:    http://localhost:5173                    ║${NC}"
if [ -n "$LOCAL_IP" ]; then
echo -e "${GREEN}║  LAN access:  http://$LOCAL_IP:5173                  ║${NC}"
fi
echo -e "${GREEN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Press Ctrl+C to stop all services                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

"$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
print_success "Backend started (PID: $BACKEND_PID)"

wait $BACKEND_PID
BACKEND_EXIT_CODE=$?
echo ""
echo "Backend process exited (code: $BACKEND_EXIT_CODE)"
