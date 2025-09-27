

"""ZenetHunter backend entrypoint (FastAPI).

This module exposes `app` for ASGI servers (e.g. `uvicorn app.main:app`).
It follows FastAPI's recommended multi-file layout by keeping the application
factory and top‑level routes here, and mounting feature routers from subpackages.

Refs:
- Import string convention (`main:app`): https://fastapi.tiangolo.com/tutorial/first-steps/
- Bigger applications with `APIRouter` / `include_router`: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- CORS middleware usage: https://fastapi.tiangolo.com/tutorial/cors/
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:  # Optional in dev; avoid hard dependency at import time
    import uvicorn  # type: ignore
except Exception:  # pragma: no cover
    uvicorn = None  # type: ignore


# ---- Lifespan management ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401 (docstring optional)
    """App lifespan: initialize lightweight resources; tear down on shutdown."""
    # Startup tasks (keep minimal here; heavy init goes to dedicated modules)
    app.state.start_time = datetime.now(timezone.utc)
    yield
    # Shutdown tasks
    # e.g., close DB pools/message buses when they are added later


# ---- App factory ------------------------------------------------------------
APP_NAME = "ZenetHunter API"
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)


# ---- CORS (dev-friendly defaults; production should restrict origins) -------
def _parse_origins(raw: str) -> List[str]:
    # Split by comma, strip spaces, drop empties
    return [o.strip() for o in raw.split(",") if o.strip()]

_default_origins = "http://localhost:5173"
origins = _parse_origins(os.getenv("CORS_ORIGINS", _default_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Top-level routes -------------------------------------------------------
@app.get("/", tags=["meta"])  # Root placeholder
async def root() -> Dict[str, Any]:
    """Root endpoint with basic service metadata and docs pointers."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "healthz": "/healthz",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/healthz", tags=["meta"])  # Kubernetes-style health probe
async def healthz() -> Dict[str, str]:
    return {"status": "ok"}


# ---- API routers (mounted from feature modules; placeholders for now) -------
api_router = APIRouter(prefix="/api")
# Example (future):
# from app.api import devices, defense, attack, scanner
# api_router.include_router(devices.router)
# api_router.include_router(defense.router)
# api_router.include_router(attack.router)
# api_router.include_router(scanner.router)

app.include_router(api_router)


# ---- Local dev entry --------------------------------------------------------
if __name__ == "__main__" and uvicorn is not None:  # pragma: no cover
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    reload = os.getenv("APP_RELOAD", "true").lower() == "true"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
