# ZenetHunter

> Device visibility + adaptive orchestration for small/home LANs. Includes a network **Scanner**, **Dispatcher**, **Interference Engine (interface layer)**, **Defender**, **Config/State Manager**, and a **Frontend SPA**. The project focuses on **observability, access control, and lawful network defense** for your own network.

---

## Repository Layout (Monorepo)
```
.
├─ backend/            # Python backend (FastAPI): API, WS, dispatcher, state/config, event bus
│   └─ app/core/
│       ├─ platform/   # Platform detection (Linux/macOS/Windows)
│       └─ engine/
│           ├─ features_macos.py  # macOS-specific network features
│           └─ macos_defense.py    # macOS defense engine (pfctl)
├─ frontend/           # Frontend SPA (Vite + React + TypeScript)
├─ deploy/             # Deployment scripts and documentation
├─ docs/               # Docs site (Getting Started, Architecture, APIs, Errors, Data Model, Guides)
├─ .github/            # CI workflows
└─ README.md           # This file
```

## Platform Support

ZenetHunter supports multiple platforms with automatic detection:

- **Linux**: Full support with iptables defense engine
- **macOS**: Full support with pfctl defense engine (see [README-MACOS.md](README-MACOS.md))
- **Windows**: Full support with Windows Firewall (netsh) defense engine

The system automatically detects the platform and selects the appropriate implementation.

> See `/docs/index.md` for the documentation landing page.

---

## Quick Start (dev; minimal)  
These commands are for **development**. Production/container usage lives in `deploy/`.

### 1) Backend (dev)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The `uvicorn app.main:app` import string follows the FastAPI/Uvicorn convention (`main` module, `app = FastAPI()` object). During development you can enable `--reload`.

### 2) Clean Cache (optional)

Before running after code changes, you may want to clear all caches:

**Python script (cross-platform, recommended):**
```bash
python clean-cache.py              # Clean all caches (excludes DB and venv)
python clean-cache.py --all        # Clean everything including DB and venv
python clean-cache.py --db         # Also clean database files
python clean-cache.py --venv       # Also clean virtual environments
```

**Shell script (Linux/macOS):**
```bash
./clean-cache.sh [--all] [--db] [--venv]
```

**Batch script (Windows):**
```cmd
clean-cache.bat [--all] [--db] [--venv]
```

### 3) Frontend (dev)
```bash
cd frontend
npm ci  # or npm install / pnpm i / bun install
npm run dev
```
Vite's dev server defaults to port **5173** and can be customized (e.g. `--host 0.0.0.0`).

### 3) Docker Deployment (Recommended)

ZenetHunter provides multiple ways to run with Docker, ensuring the latest code (including uncommitted changes) is always used.

#### Prerequisites

- Docker Engine 20.10+ and Docker Compose v2.0+
- Git (for version detection, optional)
- At least 2GB free disk space

#### Quick Start with Scripts

**Option 1: One-Command Start (Recommended)**
```bash
./docker-run.sh start
```
This script automatically:
- Builds images with `--no-cache` to ensure latest code
- Sets build timestamps and version tags
- Starts all services (backend, frontend, database)

**Option 2: Build Separately**
```bash
# Build images with latest code
./docker-build.sh

# Then start services
docker compose up -d
```

**Option 3: Rebuild and Restart**
```bash
./docker-run.sh rebuild
```
This rebuilds all images with latest code and restarts services.

#### Manual Docker Compose

If you prefer using `docker compose` directly:

```bash
# Build with latest code (no cache)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
BUILD_VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
docker compose build --no-cache --build-arg BUILD_DATE="$BUILD_DATE" --build-arg BUILD_VERSION="$BUILD_VERSION"

# Start services
docker compose up -d
```

#### Available Script Commands

**docker-run.sh** - Main orchestration script:
```bash
./docker-run.sh start      # Build and start all services
./docker-run.sh stop       # Stop all services
./docker-run.sh restart    # Restart services (no rebuild)
./docker-run.sh rebuild    # Rebuild and restart (uses latest code)
./docker-run.sh logs       # View logs (follow mode)
./docker-run.sh status     # Check service status
./docker-run.sh build      # Build images only (no cache)
```

**docker-build.sh** - Dedicated build script:
```bash
./docker-build.sh          # Build all services
./docker-build.sh backend  # Build only backend
./docker-build.sh frontend # Build only frontend
```

#### Production Deployment

For production deployment using the enhanced configuration:

```bash
cd deploy
./start.sh
```

This uses `deploy/docker-compose.yml` with additional security features, resource limits, and health checks.

#### Important Notes

- **Latest Code**: All build scripts use `--no-cache` to ensure your latest local code (including uncommitted changes) is included in the Docker images.
- **Build Args**: The scripts automatically generate `BUILD_DATE` and `BUILD_VERSION` (includes `--dirty` flag for uncommitted changes).
- **Code Changes**: Any local modifications (committed or uncommitted) will be included in the build.
- **Cache**: Docker layer caching is disabled to guarantee fresh builds. For faster rebuilds during development, you can remove `--no-cache` but this may use stale code.
- **Production**: For production deployment, see `/deploy/README.md` for advanced configuration, security hardening, and NAS-specific notes.

#### Access Points

After starting services, access:
- **Frontend**: http://localhost:1226
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/healthz
- **OpenAPI Schema**: http://localhost:8000/openapi.json

#### Troubleshooting

**Issue: Changes not reflected after rebuild**
- Solution: Ensure you're using `--no-cache` flag. Run `./docker-run.sh rebuild` to force a complete rebuild.

**Issue: Port already in use**
- Solution: Stop conflicting services or change ports in `docker-compose.yml`:
  - Frontend: `1226:8080` → `1227:8080`
  - Backend: `8000:8000` → `8001:8000`

**Issue: Backend not accessible (connection refused)**
- **Symptoms**: Cannot access `http://localhost:8000/healthz` or `http://localhost:8000/docs`
- **Diagnosis**: Run the health check script:
  ```bash
  cd deploy
  ./check-backend.sh
  ```
- **Common causes**:
  1. **Database connection failed**: Backend cannot connect to PostgreSQL
     - Check database is running: `docker ps | grep zh-db`
     - Check database port is exposed: `docker port zh-db` (should show `5432/tcp`)
     - Check backend logs: `docker logs zh-backend --tail 50`
     - Verify DATABASE_URL uses `localhost:5432` (not `db:5432`) when using host network mode
  2. **Port already in use**: Another service is using port 8000
     - Check: `lsof -i :8000` or `netstat -an | grep 8000`
     - Stop conflicting service or change APP_PORT in docker-compose.yml
  3. **Container not started**: Backend container failed to start
     - Check container status: `docker ps -a | grep zh-backend`
     - View logs: `docker logs zh-backend`
     - Restart: `docker compose restart backend`
- **Solution**: 
  ```bash
  # Stop all services
  docker compose down
  
  # Start database first
  docker compose up -d db
  
  # Wait for database to be ready (check logs)
  docker logs -f zh-db
  
  # Start backend
  docker compose up -d backend
  
  # Check backend logs
  docker logs -f zh-backend
  ```

**Issue: "Failed to start scan: Network Error" or scan not working**
- **Current Configuration**: The default configuration uses **root user** for maximum compatibility with network scanning.
  
  **⚠️ Security Notice**: 
  - The backend container runs as **root user (UID 0)** to enable network scanning functionality
  - This reduces container isolation security but is necessary for Scapy to create raw sockets
  - Combined with `network_mode: "host"`, the container has full access to the host network
  - **For production environments**, consider:
    - Running the backend directly on the host (not in a container)
    - Using a dedicated network scanning service with proper isolation
    - Implementing additional security measures (firewall rules, network segmentation)
  
- **Current Docker Configuration** (already applied):
  ```yaml
  backend:
    user: "0"  # Root user for network scanning
    network_mode: "host"  # Host network access
    cap_add:
      - NET_RAW    # Raw socket operations
      - NET_ADMIN   # Network administration
  ```
  
- **Why Root is Required**:
  - Scapy needs to create raw sockets for network packet injection
  - Raw sockets require root privileges or specific Linux capabilities
  - Even with NET_RAW capability, some operations still require root
  - Root + host network mode provides the most reliable network scanning experience
  
- **Verification**: Check if configuration is correct:
  ```bash
  # Check if running as root
  docker exec zh-backend id
  # Should show: uid=0(root) gid=0(root)
  
  # Check network mode
  docker inspect zh-backend | grep NetworkMode
  # Should show: "NetworkMode": "host"
  
  # Check capabilities
  docker inspect zh-backend | grep -A 5 "CapAdd"
  
  # Test scan functionality
  docker logs -f zh-backend
  ```
  
- **If Scan Still Fails**:
  1. Ensure Docker has permission to use host network mode
  2. Check that no firewall is blocking raw socket creation
  3. Verify Scapy is installed: `docker exec zh-backend python -c "import scapy; print(scapy.__version__)"`
  4. Check system logs: `docker logs zh-backend | grep -i "scan\|network\|permission"`
  
- **Security Recommendations**:
  - Only run this container on trusted networks
  - Use firewall rules to restrict container network access if needed
  - Regularly update Docker and container images
  - Monitor container logs for suspicious activity
  - Consider network segmentation to isolate the scanning service

**Issue: Permission denied on scripts**
- Solution: Make scripts executable: `chmod +x docker-run.sh docker-build.sh`

**Issue: Build fails with "module not found"**
- Solution: Ensure all dependencies are listed in `requirements.txt` (backend) or `package.json` (frontend).

The images follow Docker **best practices** (multi-stage builds, .dockerignore, non-root when feasible, read-only filesystems where possible).

---

## Modules
- **Scanner**: subnet scanning, device discovery, topology capture; reports to the state manager.
- **Dispatcher**: receives user/strategy intents and orchestrates Scanner, Interference Engine, and **Defender**.
- **Interference Engine (interface layer)**: normalized hooks for interference actions (implementation gated by env/permissions; ships as a safe placeholder).
- **Defender**: lawful defense primitives (e.g., SYN proxying, traffic shaping, DNS RPZ sinkholing, walled-garden, TCP resets) aggregated behind a unified API.
- **Config/State Manager**: canonical models for devices/topology/allow-deny lists/logs with read/write APIs.
- **Frontend SPA**: device list, topology, policy triggers, and real‑time status via WebSocket.

> API & message formats: see **Module Interface Spec**.  
> Data model: see **Data Structures & DB Model**.

---

## Developer Guide Entrypoints
- **Getting Started**: `/docs/getting-started.md`
- **Architecture**: `/docs/architecture.md`
- **Module Interface Spec**: `/docs/module-apis.md`
- **AI Dispatcher Design**: `/docs/ai-dispatcher.md`
- **Defender Module**: `/docs/defender.md`
- **Errors & Exceptions**: `/docs/errors-and-exceptions.md`
- **Data Structures & DB Model**: `/docs/data-model.md`
- **Deployment**: `/deploy/README.md`

> Filenames may differ while docs are being migrated—treat these as pointers.

---

## Conventions
- **Commits**: Conventional Commits (e.g., `feat:`, `fix:`, with BREAKING CHANGE footers).
- **Versioning**: SemVer (`MAJOR.MINOR.PATCH`).
- **Editor style**: EditorConfig enforced (charset/line endings/indent).
- **Configuration**: 12‑Factor—store config in **environment variables**.

---

## Compliance & Scope
ZenetHunter is for **your own network**: observability, access control, and lawful defensive measures. It must **not** be used against networks you don't own/manage.

---

## License
MIT — see `/LICENSE`.
