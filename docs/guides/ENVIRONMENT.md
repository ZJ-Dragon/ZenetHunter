# Environment Variables

This page consolidates all runtime and system-level environment variables used by ZenetHunter. Configuration follows the 12‑Factor pattern: values are read from environment variables first, with optional `backend/.env` overrides for local development.

## How configuration is loaded
- Priority: **system environment** → **`backend/.env`** → **code defaults** (via `pydantic-settings`).
- Default `.env` location: create `backend/.env` if you prefer file-based values for local runs.
- `start-local.sh` preloads sensible defaults when missing (e.g., `APP_ENV=development`, `APP_HOST=0.0.0.0`, `APP_PORT=8000`, `LOG_LEVEL=info`, `DATABASE_URL=sqlite+aiosqlite:///./data/zenethunter.db`, and a permissive `CORS_ALLOW_ORIGINS`).

## Local environment detection (`start-local.sh`)
The launcher auto-detects your Python environment and falls back cautiously:
1) `CONDA_DEFAULT_ENV` set and not `base` → use the conda env.
2) `VIRTUAL_ENV` set → use the active venv.
3) `.venv/` directory exists → auto-activate and use it.
4) Otherwise prompt to continue in the system interpreter (not recommended).

**Recommended workflows**
- Conda: `conda env create -f environment.yml && conda activate zenethunter && ./start-local.sh`
- venv: `python3 -m venv .venv && source .venv/bin/activate && ./start-local.sh`
- Need full network scanning? run with `sudo ./start-local.sh` so raw-socket operations are allowed.

## System-level and runtime variables
| Variable | Set by | Purpose / Used in |
| --- | --- | --- |
| `CONDA_DEFAULT_ENV` | Conda | Environment detection in `start-local.sh`; `base` is treated as "no env" to avoid pollution. |
| `VIRTUAL_ENV` | Python venv | Environment detection in `start-local.sh`; used to decide install target. |
| `PYTHONPATH` | User/System | Optional import path additions; normally unnecessary if dependencies are installed. |
| `PATH` | System/Shell | Command discovery (`python3`, `node`, `npm`, `conda`, `lsof`, `netstat`) in scripts. |
| `EUID` / `id -u` | Shell | Detects root privileges for raw network scanning in `start-local.sh`. |
| `DOCKER_CONTAINER` / `container` | Docker runtime | Docker detection in `backend/app/core/platform/detect.py` to adjust platform behavior. |
| `LOCAL_IP` (computed) | `start-local.sh` | Derived from `ip`/`ifconfig`; appended to `CORS_ALLOW_ORIGINS` so the frontend on your LAN works. |
| `BACKEND_PID` / `FRONTEND_PID` | `start-local.sh` | Process IDs tracked for cleanup after launching Uvicorn and Vite. |
| `npm_package_version` | npm | Used in `frontend/vite.config.ts` to stamp `__APP_VERSION__` at build time. |

## Application configuration variables
All variables below are read by `backend/app/core/config.py` (Pydantic Settings). Types are strings unless noted.

### Application basics
- `APP_ENV` (default `development`): `development` | `staging` | `production`; affects logging defaults and CORS expectations.
- `API_TITLE` / `APP_NAME` (default `ZenetHunter API`): Display name in API docs.
- `API_VERSION` / `APP_VERSION` (default `0.1.0`): Version string.
- `APP_HOST` (default `0.0.0.0`): Bind address for Uvicorn.
- `APP_PORT` (default `8000`): API port.

### Logging
- `LOG_LEVEL` (default `info`; auto-upgraded to `debug` in development and `warning` in production if unset). Allowed: `debug`, `info`, `warning`, `error`, `critical`.

### Security & CORS
- `SECRET_KEY` (default insecure placeholder): **Change for production.**
- `ACTIVE_DEFENSE_ENABLED` (bool, default `false`): Global kill-switch for active defense routines.
- `ACTIVE_DEFENSE_READONLY` (bool, default `false`): Query-only mode.
- `CORS_ALLOW_ORIGINS` / `CORS_ORIGINS` (CSV; default `http://localhost:5173` in code, expanded in `start-local.sh` with local IP): Allowed frontend origins.

### Database
- `DATABASE_URL` (default `None` → SQLite at `backend/data/zenethunter.db`; `start-local.sh` sets an explicit SQLite URL if missing): SQLAlchemy DSN.

### Router integration
- `ROUTER_ADAPTER` (default `dummy`): e.g., `dummy`, `xiaomi`, `tp-link`.
- `ROUTER_HOST` / `ROUTER_PORT`: Router API address and port.
- `ROUTER_USERNAME` / `ROUTER_PASSWORD`: Credentials for router adapter.

### Webhook verification
- `WEBHOOK_SECRET` (default `dev-webhook-secret`): HMAC secret for webhook signatures.
- `WEBHOOK_TOLERANCE_SEC` (int, default `300`): Timestamp tolerance (seconds).

### Scanning configuration
- `SCAN_MODE` (default `hybrid`): `hybrid` (cache-based) or `full` (full subnet).
- `SCAN_ALLOW_FULL_SUBNET` (bool, default `false`): Allow resource-heavy full scans.
- `SCAN_RANGE` (default `192.168.1.0/24`): CIDR for full scans.
- `SCAN_TIMEOUT_SEC` (int, default `30`): Full scan timeout.
- `SCAN_CONCURRENCY` (int, default `10`): Max concurrent probes.
- `SCAN_INTERVAL_SEC` (int/empty, default `None`): Auto-scan interval (seconds).
- `SCAN_REFRESH_WINDOW` (int, default `10`): Refresh window (hybrid mode).
- `SCAN_REFRESH_CONCURRENCY` (int, default `10`): Concurrent refresh probes.
- `SCAN_REFRESH_TIMEOUT` (float, default `1.0`): Refresh probe timeout per device.

### Feature flags (enrichment)
- `FEATURE_MDNS` (bool, default `true`): Enable mDNS enrichment.
- `FEATURE_SSDP` (bool, default `true`): Enable SSDP/UPnP enrichment.
- `FEATURE_NBNS` (bool, default `false`): Enable NBNS (Windows discovery).
- `FEATURE_SNMP` (bool, default `false`): Enable SNMP queries (requires creds).
- `FEATURE_ACTIVE_PROBE` (bool, default `true`): Enable active probing (HTTP/Telnet/SSH/Printer/IoT).
- `FEATURE_HTTP_IDENT` (bool, default `true`): Enable safe HTTP/HTTPS identification probes.
- `FEATURE_PRINTER_IDENT` (bool, default `true`): Enable printer identification when hints are present.
- External recognition providers have been removed; no outbound lookups are performed.

## Example `backend/.env`
```bash
# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=debug

# Security
SECRET_KEY=change-me-32-bytes-min
ACTIVE_DEFENSE_ENABLED=false
ACTIVE_DEFENSE_READONLY=false
CORS_ALLOW_ORIGINS=http://localhost:5173

# Database (optional; SQLite used if unset)
# DATABASE_URL=postgresql://user:password@localhost:5432/zenethunter

# Scanning
SCAN_MODE=hybrid
SCAN_ALLOW_FULL_SUBNET=false
SCAN_RANGE=192.168.31.0/24

# Feature Flags
FEATURE_MDNS=true
FEATURE_SSDP=true
FEATURE_ACTIVE_PROBE=true
FEATURE_HTTP_IDENT=true
FEATURE_PRINTER_IDENT=true
```

## Production checklist
- Set `APP_ENV=production` and `LOG_LEVEL` to `warning` or `error`.
- Generate a strong `SECRET_KEY`; store secrets securely.
- Explicitly configure `CORS_ALLOW_ORIGINS` for your frontend domains.
- Provide a non-SQLite `DATABASE_URL` if required.
- Enable `ACTIVE_DEFENSE_ENABLED` only if intended.

## Troubleshooting
- Variables not loading: ensure `.env` lives in `backend/`, use `KEY=value` (no spaces), restart the server after changes.
- Env-specific defaults: `LOG_LEVEL` auto-switches by `APP_ENV` only when not explicitly set.
- Verify current settings: `cd backend && python -m app.core.config` (sensitive values are masked).
- Local CORS: `start-local.sh` appends your LAN IP to `CORS_ALLOW_ORIGINS`; rerun the script if your IP changes.
