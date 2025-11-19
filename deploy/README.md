# Deploying ZenetHunter (Local & UGREEN NAS)

This guide shows how to **build and run** ZenetHunter with Docker Compose on a developer workstation and on a **UGREEN NASync DXP4800 Plus (UGOS Pro)**.

> TL;DR: use the provided multi‑stage Dockerfiles and `docker-compose.yml` under `/deploy`. Configure runtime via environment variables (see `env/.env.example`).

---

## 1) Prerequisites

- **Docker & Compose** installed on your machine (or available on your UGREEN NAS via its Docker app / Portainer). On UGREEN, UGOS Pro provides a Docker app and you can also install **Portainer** as an optional management UI.
- **Hardware** context (DXP4800 Plus): Intel® Pentium® Gold 8505 (5C/6T), 8GB DDR5 (expandable to 64GB), UGOS Pro. This informs worker counts and resource limits.

---

## 2) Local build & run (developer machine)

From the repository root:

```bash
# 1) Prepare environment
cd deploy
cp -n env/.env.example env/.env   # edit values as needed

# 2) Build images (multi-stage: backend & frontend)
docker compose build

# 3) Start services (db → backend → frontend)
docker compose up -d

# 4) Check health
docker compose ps
# or curl http://localhost:8000/healthz

# 5) Stop
# docker compose down
```

CI note: the GitHub Actions "image-check" workflow performs build-only validation (pull latest bases, no push); locally prefer `docker compose build` for verification.

- Default container ports: **8000/tcp** (backend API), **8080/tcp** (frontend via nginx). Host mapping (compose default): **1226 → 8080** for the frontend. Health checks are baked into both images (backend `/healthz`, frontend root `/`).

---

## 3) UGREEN NAS (UGOS Pro) deployment

There are two common ways to run containers on UGREEN NAS:

### Option A — via NAS Docker/Compose (CLI)

1. **Enable SSH** on your NAS (UGOS settings) and SSH in as an admin user.
2. Ensure the **Docker app** is available/active on UGOS. (UGREEN's App Center exposes system apps, including Docker.)
3. Copy your project to the NAS (e.g., to a shared folder) or **git clone** on the NAS.
4. Inside the project's `deploy/` dir, create runtime env:
   ```bash
   cp -n env/.env.example env/.env
   vi env/.env  # set VITE_API_BASE, CORS_ORIGINS, etc.
   ```
5. Build & start:
   ```bash
   docker compose build
   docker compose up -d
   ```
6. Access:
  - Frontend: `http://<NAS-IP>:1226/`  (mapped to container 8080)
  - API: `http://<NAS-IP>:8000/` (health: `/healthz`)

> Tip: Keep **volumes on SSD** (e.g., M.2) for container writable data to avoid keeping HDDs spinning and improve responsiveness. Community users recommend putting Docker app data on SSD for UGOS.

### Option B — via Portainer (UI)

1. Install Portainer on the NAS (either from UGOS' App Center if available, or by running the official container). Community guides show Portainer working well on UGREEN.
2. In Portainer, **add a stack** and paste the contents of `deploy/docker-compose.yml`. Adjust environment variables and volumes to your dataset paths.
3. Deploy the stack. Use Portainer's **Health** and **Logs** views to verify service readiness.

> Note: Some users report confusion mapping `/var/run/docker.sock` in UGOS. If using Portainer's **local** socket, ensure the Docker daemon is running and the socket is accessible; otherwise use the "**Agent**" deployment model.

---

## 4) Ports, volumes & restart policy (overview)

| Service   | Container Port | Host Port (default) | Volumes (default)                     | Restart policy        |
|-----------|-----------------|---------------------|---------------------------------------|-----------------------|
| backend   | 8000            | 8000                | (binds not required yet)              | `unless-stopped`      |
| frontend  | 8080            | 1226                | `dist/` baked into image              | `unless-stopped`      |
| db        | 5432            | *not published*     | `db_data:/var/lib/postgresql/data`    | `unless-stopped`      |

- Edit `deploy/docker-compose.yml` to change **port mappings** or move volumes to SSD pools. Health checks gate service readiness, and `depends_on` is configured.

---

## 5) Configuration via environment (.env)

All runtime configuration is environment‑driven (12‑Factor). The application automatically loads configuration from environment variables and optionally from `.env` files.

### Quick Setup

1. Copy the example file:
   ```bash
   cd deploy
   cp env/.env.example env/.env
   ```

2. Edit `env/.env` and customize values for your environment

3. The application will automatically load variables from `env/.env` when using Docker Compose

### Environment-Specific Defaults

The application applies different default values based on `APP_ENV`:

- **Development** (`APP_ENV=development`):
  - Log level: `debug` (if not explicitly set)
  - CORS: Allows common dev ports

- **Staging** (`APP_ENV=staging`):
  - Log level: `info` (if not explicitly set)

- **Production** (`APP_ENV=production`):
  - Log level: `warning` (if not explicitly set)
  - CORS: **Must be explicitly configured** (warns if not set)

### Key Configuration Variables

| Variable | Example | Description |
|---|---|---|
| `APP_ENV` | `production` | Environment: `development`/`staging`/`production` |
| `CORS_ALLOW_ORIGINS` | `http://<NAS-IP>:8080` | Comma-separated CORS origins (for NAS, include nginx host) |
| `DATABASE_URL` | `postgresql://zenethunter:zenethunter@db:5432/zenethunter` | PostgreSQL DSN (Compose uses service name `db`) |
| `LOG_LEVEL` | `info` | Log level: `debug`/`info`/`warning`/`error`/`critical` |
| `API_TITLE` | `ZenetHunter API` | API title (OpenAPI docs) |
| `API_VERSION` | `0.1.0` | API version (OpenAPI docs) |

**Note**: Environment variables set directly in `docker-compose.yml` take precedence over `.env` file values.

See also: `backend/app/core/config.py` and `backend/README.md`.

---

## 6) Scaling, resources & CPU on DXP4800 Plus

- The DXP4800 Plus uses an **Intel Pentium Gold 8505** (5 cores / 6 threads). Start Uvicorn with a modest worker count (1–2) and prefer async I/O. Avoid heavy CPU tasks on NAS unless scheduled.
- Keep scanner intervals conservative and consider pinning noisy workloads to SSD where possible. Community advice suggests Docker workloads on M.2 SSD for snappy UX.

---

## 7) Upgrades & rollback

- Pull the latest code, then rebuild:
  ```bash
  docker compose pull   # if using remote images later
  docker compose build  # for local builds
  docker compose up -d --no-deps --build backend frontend
  ```
- Rollback: keep previous images tagged (e.g., `:v0.1.0`), or `docker image ls` and `docker compose up -d` with the known‑good tag.

---

## 8) Troubleshooting

- **Frontend up, API 404** → check `VITE_API_BASE` and **CORS_ORIGINS**; verify backend `/healthz`.
- **Compose complains about `name:`** → some older Compose versions don't support top‑level `name`. Set `COMPOSE_PROJECT_NAME=zenethunter` or remove `name:`.
- **Portainer cannot connect to Docker** → verify Docker daemon/socket on UGOS, or deploy the Portainer **Agent** and connect over TCP.
- **Performance (thumbnails/metadata slow)** → store container data on SSD, not HDD pools (community tip).

---

## 9) Security notes

- Expose ports only on trusted LANs; use NAS firewall if available.
- Keep images up to date; CI uses build-only validation to catch issues early.
- **Non-root** by default: backend & frontend run as non-root; Compose sets `user: "101:101"`, `read_only: true`, and `tmpfs: /tmp`.
- Never commit real secrets; inject via environment or secret stores.

---

## 10) References & further reading

- UGREEN NASync DXP4800 Plus product page/specs (UGOS Pro, CPU/RAM, bays).
- UGOS Pro – App Center / System apps overview (incl. Docker).
- Portainer on UGREEN NAS (community how‑to).
- Community tips on Docker storage (use SSD for app data).
