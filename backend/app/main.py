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

import asyncio
import logging
import signal
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
from app.core.middleware import (
    ErrorHandlerMiddleware,
    get_correlation_id,
    sanitize_validation_errors,
)
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
    scheduler,
    topology,
)

logger = logging.getLogger(__name__)

try:  # Optional in dev; avoid hard dependency at import time
    import uvicorn  # type: ignore
except Exception:  # pragma: no cover
    uvicorn = None  # type: ignore


# ---- Lifespan management ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401 (docstring optional)
    """App lifespan: initialize lightweight resources; tear down on shutdown."""
    # Setup signal handlers for graceful shutdown
    # Note: Uvicorn handles signals internally, but we can still set up handlers
    # for custom cleanup logic. The actual shutdown is handled by Uvicorn.
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        shutdown_event.set()
        # Trigger shutdown by setting the event
        # Uvicorn will handle the actual shutdown

    # Register signal handlers (only on main thread)
    # Note: signal handlers must be registered in the main thread
    # Uvicorn runs in the main thread, so this should work
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except ValueError:
        # Signals can only be registered in the main thread
        # If we're not in the main thread, skip signal registration
        logger.warning("Cannot register signal handlers (not in main thread)")

    # Startup tasks (keep minimal here; heavy init goes to dedicated modules)
    setup_logging()  # Initialize structured logging
    app.state.start_time = datetime.now(UTC)
    app.state.shutdown_event = shutdown_event

    # Initialize database with retry logic
    from app.core.config import get_settings
    from app.core.database import get_database_url, init_db

    max_retries = 5
    retry_delay = 2
    db_url = get_database_url()
    # Mask password in URL for logging
    safe_url = db_url.split("@")[-1] if "@" in db_url else db_url
    # Also get the original URL from settings for better error messages
    settings = get_settings()
    db_host = (
        "localhost"
        if settings.database_url and "localhost" in settings.database_url
        else "unknown"
    )

    for attempt in range(max_retries):
        try:
            logger.info(
                f"Initializing database connection "
                f"(attempt {attempt + 1}/{max_retries}) to {safe_url}"
            )
            await init_db()
            # Use print as fallback if logger fails (shouldn't happen, but safety first)
            try:
                logger.info("Database initialized successfully")
            except Exception as log_err:
                # If logging fails, at least print to stdout
                print(
                    f"Database initialized successfully (logging failed: {log_err})",
                    flush=True,
                )
            break
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database initialization failed "
                    f"(attempt {attempt + 1}/{max_retries}): "
                    f"{error_type}: {error_msg}. Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"Database initialization failed after {max_retries} attempts. "
                    f"Error: {error_type}: {error_msg}. "
                    f"Database: {safe_url}. "
                    f"Troubleshooting: 1) Check database container: "
                    f"'docker ps | grep zh-db', "
                    f"2) Check port exposure: 'docker port zh-db', "
                    f"3) Test connection: 'psql -h {db_host} -p 5432 "
                    f"-U zenethunter -d zenethunter', "
                    f"4) Check backend logs for details."
                )
                raise

    try:
        yield
    finally:
        # Shutdown tasks - this runs when the app is shutting down
        logger.info("Application shutdown initiated, cleaning up resources...")

        # Close all WebSocket connections first
        try:
            from app.services.websocket import get_connection_manager

            ws_manager = get_connection_manager()
            await ws_manager.close_all()
        except Exception as e:
            logger.warning(f"Error closing WebSocket connections: {e}")

        # Cancel all active tasks gracefully
        logger.info("Cancelling active tasks...")
        try:
            from app.services.attack import AttackService
            from app.services.scanner import ScannerService

            # Get service instances and cancel their tasks
            scanner = ScannerService()
            if hasattr(scanner, "active_tasks"):
                for scan_id, task in list(scanner.active_tasks.items()):
                    if not task.done():
                        logger.info(f"Cancelling scan task {scan_id}")
                        task.cancel()

            attack = AttackService()
            if hasattr(attack, "active_tasks"):
                for mac, task in list(attack.active_tasks.items()):
                    if not task.done():
                        logger.info(f"Cancelling attack task for {mac}")
                        task.cancel()

            # Wait a bit for tasks to cancel (with timeout)
            try:
                all_tasks = []
                if hasattr(scanner, "active_tasks"):
                    all_tasks.extend(scanner.active_tasks.values())
                if hasattr(attack, "active_tasks"):
                    all_tasks.extend(attack.active_tasks.values())

                if all_tasks:
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*all_tasks, return_exceptions=True),
                            timeout=2.0,
                        )
                    except TimeoutError:
                        logger.warning(
                            "Some tasks did not cancel within timeout, "
                            "continuing shutdown..."
                        )
            except Exception as e:
                logger.warning(f"Error waiting for tasks to cancel: {e}")
        except Exception as e:
            logger.warning(f"Error during task cleanup: {e}", exc_info=True)

        # Close database
        try:
            from app.core.database import close_db

            await close_db()
        except Exception as e:
            logger.warning(f"Error closing database: {e}")

        logger.info("Shutdown complete")


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
# Allow file:// protocol for local HTML file access
cors_origins = settings.cors_origins if settings.cors_origins != ["*"] else ["*"]
# Add null origin for file:// protocol support
if "*" not in cors_origins:
    cors_origins = list(cors_origins) + [
        "null"
    ]  # "null" is the origin for file:// protocol

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
        extra={"errors": sanitize_validation_errors(exc.errors())},
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
        extra={
            "errors": sanitize_validation_errors(getattr(exc, "errors", lambda: [])())
        },
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
api_router.include_router(scheduler.router)
api_router.include_router(integration_router.router)
api_router.include_router(integration_webhooks.router)

app.include_router(api_router)


# ---- Local dev entry --------------------------------------------------------
if __name__ == "__main__" and uvicorn is not None:  # pragma: no cover
    host = settings.app_host
    port = settings.app_port
    reload = settings.app_env == "development"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
