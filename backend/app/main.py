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

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes import health

try:  # Optional in dev; avoid hard dependency at import time
    import uvicorn  # type: ignore
except Exception:  # pragma: no cover
    uvicorn = None  # type: ignore


# ---- Lifespan management ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401 (docstring optional)
    """App lifespan: initialize lightweight resources; tear down on shutdown."""
    # Startup tasks (keep minimal here; heavy init goes to dedicated modules)
    app.state.start_time = datetime.now(UTC)
    yield
    # Shutdown tasks
    # e.g., close DB pools/message buses when they are added later


# ---- App factory ------------------------------------------------------------
settings = get_settings()

APP_DESCRIPTION = """
ZenetHunter backend API for network security scanning and interference management.

## Features

* Network device scanning and discovery
* Device topology visualization
* Automated interference strategies
* Real-time status monitoring via WebSocket

## API Documentation

* **Swagger UI**: `/docs` - Interactive API documentation
* **ReDoc**: `/redoc` - Alternative API documentation
* **OpenAPI JSON**: `/openapi.json` - Machine-readable API specification
"""

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
    # OpenAPI metadata
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---- CORS (dev-friendly defaults; production should restrict origins) -------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Top-level routes -------------------------------------------------------
@app.get("/", tags=["meta"])  # Root placeholder
async def root() -> dict[str, Any]:
    """Root endpoint with basic service metadata and docs pointers."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "healthz": "/healthz",
        "time": datetime.now(UTC).isoformat(),
    }


# ---- API routers (mounted from feature modules) ----------------------------
# Health check router
app.include_router(health.router)

# API router for future feature modules
api_router = APIRouter(prefix="/api")
# Example (future):
# from app.routes import devices, topology, scanner, attack
# api_router.include_router(devices.router)
# api_router.include_router(topology.router)
# api_router.include_router(scanner.router)
# api_router.include_router(attack.router)

app.include_router(api_router)


# ---- Local dev entry --------------------------------------------------------
if __name__ == "__main__" and uvicorn is not None:  # pragma: no cover
    host = settings.app_host
    port = settings.app_port
    reload = settings.app_env == "development"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
