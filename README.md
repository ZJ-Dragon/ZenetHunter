# ZenetHunter

> Device visibility + adaptive orchestration for small/home LANs. Includes a network **Scanner**, **Dispatcher**, **Interference Engine (interface layer)**, **Defender**, **Config/State Manager**, and a **Frontend SPA**. The project focuses on **observability, access control, and lawful network defense** for your own network.

> Safety notice: the repo includes network-scanning and active-interference scripts. Use only on networks you own or are expressly authorized to test—misuse may be illegal.

---

## Instructions for AI Agents

Agents must read `AGENT/` before modifying this repository. Do not change code, contracts, or documentation outside `AGENT/` until the required AGENT files have been read.

Required reading order:
1. `AGENT/memory/project-purpose.md`
2. `AGENT/rules/safety-context.md`
3. `AGENT/bridge/*`
4. `AGENT/content/*`
5. `AGENT/tasks/current-branch-plan.md`

`AGENT/` defines repository-local memory, safety boundaries, bridge contracts, repository maps, and current branch coordination. Its safety context is local to this repository only and must not be generalized into any reusable global exemption pattern.

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
├─ docs/               # Documentation (active defense, API, active probe, external services, platform/env guides)
├─ .github/            # CI workflows
└─ README.md           # This file
```

## Platform Support

ZenetHunter supports multiple platforms with automatic detection:

- **Linux**: Full support with iptables defense engine
- **macOS**: Full support with pfctl defense engine (see [macOS guide](docs/guides/README-MACOS.md))
- **Windows**: Full support with Windows Firewall (netsh) defense engine (see [Windows guide](docs/guides/README-WINDOWS.md))

The system automatically detects the platform and selects the appropriate implementation.

> Documentation hub: [docs/index.md](docs/index.md) (English) / [docs/index.zh-CN.md](docs/index.zh-CN.md)

---

## Quick Start (dev; minimal)  
These commands are for **development**.

### 1) One-Command Start (Recommended)

The easiest way to run ZenetHunter locally:

**Linux/macOS:**
```bash
./start-local.sh              # Normal start
./start-local.sh --clean      # Clean caches before starting
./start-local.sh --clean-all  # Deep clean (including DB and venv) before starting
sudo ./start-local.sh         # Run with root privileges (recommended for full network features)
```

**Windows:**
```cmd
start-local.bat               # Normal start
start-local.bat --clean       # Clean caches before starting
start-local.bat --clean-all   # Deep clean (including DB and venv) before starting
```

The startup script automatically:
- ✅ Kills residual processes (uvicorn, vite)
- ✅ Frees occupied ports (8000, 5173)
- ✅ Cleans Python/frontend/OS caches (with `--clean`)
- ✅ Detects and activates virtual environments
- ✅ Installs/updates dependencies
- ✅ Checks and repairs database schema
- ✅ Starts both backend and frontend services
- ✅ Graceful shutdown on Ctrl+C

### 2) Manual Start (Alternative)

If you prefer manual control:

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm ci  # or npm install / pnpm i / bun install
npm run dev
```
Vite's dev server defaults to port **5173** and can be customized (e.g. `--host 0.0.0.0`).

> Docker/Compose workflows have been removed. Use the local scripts above for development runs.

---
## Modules
- **Scanner**: subnet scanning, device discovery, topology capture; reports to the state manager.
- **Dispatcher**: receives user/strategy intents and orchestrates Scanner, Interference Engine, and **Defender**.
- **Interference Engine (interface layer)**: normalized hooks for interference actions (implementation gated by env/permissions; ships as a safe placeholder).
- **Defender**: lawful defense primitives (e.g., SYN proxying, traffic shaping, DNS RPZ sinkholing, walled-garden, TCP resets) aggregated behind a unified API.
- **Config/State Manager**: canonical models for devices/topology/allow-deny lists/logs with read/write APIs.
- **Frontend SPA**: device list, topology, policy triggers, and real‑time status via WebSocket.

> API & message formats: see [docs/api/README.md](docs/api/README.md).  
> Active defense internals: see [docs/active-defense/README.md](docs/active-defense/README.md).

---

## Documentation Entrypoints
- **Docs hub**: [docs/index.md](docs/index.md) / [中文](docs/index.zh-CN.md)
- **Active Defense**: [docs/active-defense/README.md](docs/active-defense/README.md) / [中文](docs/active-defense/README.zh-CN.md)
- **Active Probe**: [docs/active-probe/ACTIVE_PROBE.md](docs/active-probe/ACTIVE_PROBE.md) / [中文](docs/active-probe/ACTIVE_PROBE.zh-CN.md)
- **API reference**: [docs/api/README.md](docs/api/README.md) / [中文](docs/api/README.zh-CN.md)
- **Platform setup**: macOS ([docs/guides/README-MACOS.md](docs/guides/README-MACOS.md) / [中文](docs/guides/README-MACOS.zh-CN.md)), Windows ([docs/guides/README-WINDOWS.md](docs/guides/README-WINDOWS.md) / [中文](docs/guides/README-WINDOWS.zh-CN.md))
- **Runtime configuration**: [docs/guides/ENVIRONMENT.md](docs/guides/ENVIRONMENT.md) / [中文](docs/guides/ENVIRONMENT.zh-CN.md)
- **External recognition services**: [docs/external-services/EXTERNAL_SERVICES.md](docs/external-services/EXTERNAL_SERVICES.md) / [中文](docs/external-services/EXTERNAL_SERVICES.zh-CN.md)
- **Privacy guardrails**: [docs/external-services/PRIVACY.md](docs/external-services/PRIVACY.md) / [中文](docs/external-services/PRIVACY.zh-CN.md)
- **Conda setup (zh)**: [docs/guides/CONDA_SETUP.md](docs/guides/CONDA_SETUP.md)
- **Force-shutdown operations (zh)**: [docs/guides/FORCE_SHUTDOWN_GUIDE.md](docs/guides/FORCE_SHUTDOWN_GUIDE.md)

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
