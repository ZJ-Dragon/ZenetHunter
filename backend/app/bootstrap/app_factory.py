"""FastAPI application factory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError, ValidationException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.bootstrap.lifecycle import lifespan
from app.core.config import get_settings
from app.core.exceptions import AppError, ErrorCode
from app.core.middleware import (
    ErrorHandlerMiddleware,
    get_correlation_id,
    sanitize_validation_errors,
)
from app.routes import (
    attack,
    auth,
    config,
    devices,
    health,
    integration_router,
    integration_webhooks,
    logs,
    observations,
    recognition,
    scan,
    topology,
)

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


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=APP_DESCRIPTION,
        lifespan=lifespan,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(ErrorHandlerMiddleware)
    _configure_cors(app, settings)
    _register_exception_handlers(app)
    _register_routes(app, settings)
    return app


def _configure_cors(app: FastAPI, settings) -> None:
    cors_origins = settings.cors_origins if settings.cors_origins != ["*"] else ["*"]
    if "*" not in cors_origins:
        cors_origins = list(cors_origins) + ["null"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_exception_handlers(app: FastAPI) -> None:
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
    ) -> JSONResponse:
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
    ) -> JSONResponse:
        app_error = AppError(
            ErrorCode.CONFIG_VALIDATION,
            detail="Request validation failed",
            http_status=422,
            extra={
                "errors": sanitize_validation_errors(
                    getattr(exc, "errors", lambda: [])()
                )
            },
        )
        return _problem_response(request, app_error)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        app_error = AppError(
            ErrorCode.API_BAD_REQUEST,
            detail=str(exc.detail) if hasattr(exc, "detail") else "Bad request",
            http_status=exc.status_code if hasattr(exc, "status_code") else 400,
        )
        return _problem_response(request, app_error)


def _register_routes(app: FastAPI, settings) -> None:
    @app.get("/", tags=["meta"])
    async def root() -> dict[str, Any]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "redoc": "/redoc",
            "healthz": "/healthz",
            "time": datetime.now(UTC).isoformat(),
        }

    app.include_router(health.router)

    api_router = APIRouter(prefix="/api")
    api_router.include_router(health.router)
    api_router.include_router(auth.router)
    api_router.include_router(devices.router)
    api_router.include_router(topology.router)
    api_router.include_router(logs.router)
    api_router.include_router(config.router)
    api_router.include_router(scan.router)
    api_router.include_router(attack.router)
    api_router.include_router(attack.legacy_router)
    api_router.include_router(recognition.router)
    api_router.include_router(integration_router.router)
    api_router.include_router(integration_webhooks.router)
    api_router.include_router(observations.router)

    app.include_router(api_router)
