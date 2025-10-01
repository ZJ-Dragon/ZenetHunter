

# ZenetHunter

> Device visibility + adaptive orchestration for small/home LANs. Includes a network **Scanner**, **Dispatcher**, **Interference Engine (interface layer)**, **Defender**, **Config/State Manager**, and a **Frontend SPA**. The project focuses on **observability, access control, and lawful network defense** for your own network.

---

## Repository Layout (Monorepo)
```
.
├─ backend/            # Python backend (FastAPI): API, WS, dispatcher, state/config, event bus
├─ frontend/           # Frontend SPA (Vite + React + TypeScript)
├─ deploy/             # Dockerfiles, docker-compose, env samples, NAS/server deployment notes
├─ docs/               # Docs site (Getting Started, Architecture, APIs, Errors, Data Model, Guides)
├─ .github/            # CI workflows
└─ README.md           # This file
```

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
The `uvicorn app.main:app` import string follows the FastAPI/Uvicorn convention (`main` module, `app = FastAPI()` object). During development you can enable `--reload`. citeturn0search0

### 2) Frontend (dev)
```bash
cd frontend
npm ci  # or npm install / pnpm i / bun install
npm run dev
```
Vite's dev server defaults to port **5173** and can be customized (e.g. `--host 0.0.0.0`). citeturn0search1turn0search15

### 3) One-Command Compose (optional)
```bash
cd deploy
docker compose up -d  # edit .env first if needed
```
The images follow Docker **best practices** (multi-stage builds, .dockerignore, non-root when feasible). citeturn0search2turn0search9

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
- **Deployment (Ugreen / Docker)**: `/deploy/README.md`

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
