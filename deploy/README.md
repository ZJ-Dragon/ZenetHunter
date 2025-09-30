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

- Default ports: **8000/tcp** (backend API), **8080/tcp** (frontend via nginx). See the mapping in `docker-compose.yml` and edit if needed. Health checks for each service are already defined. (Backend `/healthz`.)

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
  - Frontend: `http://<NAS-IP>:8080/`
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
| frontend  | 80 (nginx)      | 8080                | `dist/` baked into image              | `unless-stopped`      |
| db        | 5432            | *not published*     | `db_data:/var/lib/postgresql/data`    | `unless-stopped`      |

- Edit `deploy/docker-compose.yml` to change **port mappings** or move volumes to SSD pools. Health checks gate service readiness, and `depends_on` is configured.

---

## 5) Configuration via environment (.env)

All runtime configuration is environment‑driven (12‑Factor). Use `deploy/env/.env.example` as a template:

- **CORS_ORIGINS**: For NAS default, include the nginx host origin, e.g. `http://<NAS-IP>:8080`.
- **VITE_API_BASE**: The frontend uses this to call the API; on NAS, set `VITE_API_BASE=http://<NAS-IP>:8000`.
- **DATABASE_URL**: Compose connects backend → `db` service by name. For an external DB, replace with that DSN.
- **LOG_LEVEL**: `debug|info|warning|error|critical` (backend).

See also: `backend/app/core/config.py`.

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
- Keep images up to date. Prefer **non‑root** containers (our backend image already runs as a non‑root user).
- Never commit real secrets; inject via environment or secret stores.

---

## 10) References & further reading

- UGREEN NASync DXP4800 Plus product page/specs (UGOS Pro, CPU/RAM, bays).
- UGOS Pro – App Center / System apps overview (incl. Docker).
- Portainer on UGREEN NAS (community how‑to).
- Community tips on Docker storage (use SSD for app data).
