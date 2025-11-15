"""Error handling middleware for FastAPI.

This module provides middleware to catch exceptions and convert them to
RFC 9457 Problem Details responses, with structured logging support.

References:
- RFC 9457 Problem Details: https://www.rfc-editor.org/rfc/rfc9457.html
- FastAPI Exception Handlers: https://fastapi.tiangolo.com/tutorial/handling-errors/
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppError, ErrorCode

logger = logging.getLogger(__name__)


def get_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID from request.

    Checks for X-Correlation-Id header, otherwise generates a new UUID.

    Args:
        request: FastAPI request object

    Returns:
        Correlation ID string
    """
    correlation_id = request.headers.get("X-Correlation-Id")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    return correlation_id


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions and return Problem Details.

    Catches all exceptions, logs them with correlation_id, and returns
    RFC 9457 Problem Details JSON responses.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process request and handle exceptions.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler in chain

        Returns:
            Response (either from handler or error response)
        """
        correlation_id = get_correlation_id(request)

        try:
            response = await call_next(request)
            # Add correlation_id to response headers
            response.headers["X-Correlation-Id"] = correlation_id
            return response
        except AppError as e:
            # Known application error - log and return Problem Details
            logger.error(
                "Application error",
                extra={
                    "correlation_id": correlation_id,
                    "code": e.code.value,
                    "http_status": e.http_status,
                    "component": "api",
                    "sd": {"error_code": e.code.value, "type_uri": e.type_uri},
                },
                exc_info=True,
            )
            return self._create_problem_response(e, correlation_id, request.url.path)
        except Exception as e:
            # Unexpected error - log with full traceback
            logger.error(
                "Uncaught exception",
                extra={
                    "correlation_id": correlation_id,
                    "code": ErrorCode.INTERNAL_UNCAUGHT.value,
                    "component": "api",
                    "sd": {"exception_type": type(e).__name__},
                },
                exc_info=True,
            )
            # Create generic error response
            app_error = AppError(
                ErrorCode.INTERNAL_UNCAUGHT,
                detail="An internal server error occurred.",
            )
            return self._create_problem_response(
                app_error, correlation_id, request.url.path
            )

    def _create_problem_response(
        self, error: AppError, correlation_id: str, instance: str
    ) -> JSONResponse:
        """Create RFC 9457 Problem Details JSON response.

        Args:
            error: AppError instance
            correlation_id: Request correlation ID
            instance: Instance URI (request path)

        Returns:
            JSONResponse with Problem Details structure
        """
        # Generate instance URI with correlation_id
        instance_uri = f"/errors/{correlation_id}"

        # Build Problem Details JSON
        problem_details = error.to_problem_details(instance=instance_uri)
        problem_details["correlation_id"] = correlation_id

        return JSONResponse(
            status_code=error.http_status,
            content=problem_details,
            headers={"X-Correlation-Id": correlation_id},
        )
