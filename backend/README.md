

# ZenetHunter – Backend (FastAPI)

Backend service providing REST/WS APIs, orchestration (Scanner/Defender/Interference interface), and state/config management.

> Runtime: **Python 3.11+**. Web framework: **FastAPI**; ASGI server: **Uvicorn**. Test stack: **pytest**. Lint/format: **Ruff + Black**.

---

## 1) Quick Start (dev)

### Create and activate a virtualenv
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

### Install dependencies (editable + dev tools)
```bash
pip install -e .[dev]
```

### Run the dev server (auto-reload)
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- `app.main:app` follows the FastAPI/Uvicorn import-string convention (`main.py` module exposing `app = FastAPI()`), and `--reload` is for **development only**.
- Open **http://localhost:8000/docs** for interactive API docs (Swagger UI).

### Run tests
```bash
pytest -q
```

### Run format & lint locally
```bash
# Run the same hooks locally that CI runs
pre-commit run --all-files
# Or run tools directly
ruff check --fix . && ruff format . && black .
```

---

## 2) Configuration & Environment Variables
We follow the **12‑Factor** principle: config is provided via **environment variables**. Example variables below are **placeholders**; adjust to your environment. Create `backend/.env` locally if you prefer file-based values (gitignored).

> Never commit secrets to the repo. Prefer real environment variables in production; `.env` is only for local dev.

| Variable | Example | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment name: `development`/`staging`/`production` |
| `APP_HOST` | `0.0.0.0` | Bind host for the ASGI server (dev) |
| `APP_PORT` | `8000` | Bind port for the ASGI server (dev) |
| `LOG_LEVEL` | `info` | Log level: `debug`/`info`/`warning`/`error` |
| `API_TITLE` | `ZenetHunter API` | API title (used in OpenAPI docs) |
| `API_VERSION` | `0.1.0` | API version (used in OpenAPI docs) |
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/zenethunter` | Primary DB DSN (placeholder) |
| `SECRET_KEY` | `...` | Secret material for session/signing (do **not** commit) |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173` | Comma‑separated list for dev UI access (also accepts `CORS_ORIGINS`) |

**Implementation note (planned):** settings are loaded via `pydantic-settings` with optional `.env` support. See `app/core/config.py`.

---

## 3) Project Layout (backend)
```
backend/
├─ app/
│  ├─ __init__.py        # Package initialization
│  ├─ main.py            # FastAPI app entrypoint (creates `app`), CORS, API wiring
│  ├─ core/              # config, logging, auth, middleware
│  │  └─ config.py       # Settings (pydantic-settings) for 12-Factor config
│  ├─ routes/            # API routers organized by feature
│  │  ├─ __init__.py     # Routes package
│  │  └─ health.py       # Health check router (GET /healthz)
│  ├─ services/          # orchestration & domain services (planned)
│  └─ models/            # pydantic models / schemas (planned)
├─ tests/                # pytest test suite
│  └─ test_healthz.py    # Health check and OpenAPI docs tests
└─ pyproject.toml        # PEP 621 metadata + tool config (ruff/black/pytest)
```

---

## 4) Common Tasks (scripts – placeholder)
> We don’t ship a task runner yet; use the commands below or add `Makefile`/`poe` in a future PR.

- **Run dev server**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run unit tests**: `pytest -q`
- **Lint/format**: `pre-commit run --all-files`
- **Type check (optional)**: add `mypy` later and run `mypy app/`

---

## 5) Production Notes (pointer)
- For production, prefer a process manager (e.g., `gunicorn -k uvicorn.workers.UvicornWorker`) and **disable** `--reload`.

---

## 6) Health & Docs
- **Health check**: `GET /healthz` → `200 OK` with `{"status": "ok"}`. Used by container orchestration systems (Kubernetes, Docker healthchecks).
- **API documentation**:
  - `GET /docs` - Swagger UI (interactive API documentation)
  - `GET /redoc` - ReDoc (alternative documentation view)
  - `GET /openapi.json` - OpenAPI schema (machine-readable, for client SDK generation)

---

## 7) Troubleshooting (quick)
- **Port already in use**: change `--port` or free the port.
- **Cannot import `app.main:app`**: ensure `backend/` is the CWD and `app/main.py` exposes `app = FastAPI()`.
- **Virtualenv issues**: confirm activation (`which python` → path under `.venv`).

---

## 8) License
MIT — see `/LICENSE` at the repo root.
