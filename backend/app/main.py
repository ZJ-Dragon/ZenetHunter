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

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError, ValidationException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import AppError, ErrorCode
from app.core.logging import setup_logging
from app.core.middleware import ErrorHandlerMiddleware, get_correlation_id
from app.routes import (
    attack,
    auth,
    config,
    defender,
    devices,
    health,
    integration_router,
    integration_webhooks,
    logs,
    scan,
    topology,
)

try:  # Optional in dev; avoid hard dependency at import time
    import uvicorn  # type: ignore
except Exception:  # pragma: no cover
    uvicorn = None  # type: ignore


# ---- Lifespan management ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401 (docstring optional)
    """App lifespan: initialize lightweight resources; tear down on shutdown."""
    # Startup tasks (keep minimal here; heavy init goes to dedicated modules)
    setup_logging()  # Initialize structured logging
    app.state.start_time = datetime.now(UTC)

    # Initialize database
    from app.core.database import init_db

    await init_db()

    yield
    # Shutdown tasks
    from app.core.database import close_db

    await close_db()


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


# ---- Middleware (order matters: error handler first, then CORS) ------------
# Error handler middleware must be added first to catch all exceptions
app.add_middleware(ErrorHandlerMiddleware)

# CORS middleware (dev-friendly defaults; production should restrict origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Exception handlers (validation & HTTP) ---------------------------------
def _problem_response(request: Request, app_error: AppError) -> JSONResponse:
    correlation_id = get_correlation_id(request)
    instance_uri = f"/errors/{correlation_id}"
    body = app_error.to_problem_details(instance=instance_uri)
    body["correlation_id"] = correlation_id
    return JSONResponse(
        status_code=app_error.http_status,
        content=body,
        headers={"X-Correlation-Id": correlation_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):  # noqa: D401
    """Return RFC9457 Problem Details for request validation errors."""
    app_error = AppError(
        ErrorCode.CONFIG_VALIDATION,
        detail="Request validation failed",
        http_status=422,
        extra={"errors": exc.errors()},
    )
    return _problem_response(request, app_error)


@app.exception_handler(ValidationException)
async def validation_exception_handler_v2(
    request: Request, exc: ValidationException
):  # noqa: D401
    """Return RFC9457 Problem Details for generic ValidationException."""
    app_error = AppError(
        ErrorCode.CONFIG_VALIDATION,
        detail="Request validation failed",
        http_status=422,
        extra={"errors": getattr(exc, "errors", lambda: [])()},
    )
    return _problem_response(request, app_error)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # noqa: D401
    """Return RFC9457 Problem Details for HTTPException."""
    app_error = AppError(
        ErrorCode.API_BAD_REQUEST,
        detail=str(exc.detail) if hasattr(exc, "detail") else "Bad request",
        http_status=exc.status_code if hasattr(exc, "status_code") else 400,
    )
    return _problem_response(request, app_error)


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
api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(topology.router)
api_router.include_router(logs.router)
api_router.include_router(config.router)
api_router.include_router(scan.router)
api_router.include_router(attack.router)
api_router.include_router(defender.router)
api_router.include_router(integration_router.router)
api_router.include_router(integration_webhooks.router)

app.include_router(api_router)


# ---- Local dev entry --------------------------------------------------------
if __name__ == "__main__" and uvicorn is not None:  # pragma: no cover
    host = settings.app_host
    port = settings.app_port
    reload = settings.app_env == "development"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
