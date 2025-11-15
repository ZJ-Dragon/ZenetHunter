"""Application exceptions and error codes.

This module defines custom exception classes and error code enums following
RFC 9457 Problem Details and the project's error handling specification.

References:
- RFC 9457 Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457.html
- OpenTelemetry Exception Semantics: https://opentelemetry.io/docs/specs/semconv/exceptions/
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import status


class ErrorCode(str, Enum):
    """Stable error codes organized by domain.

    Format: DOMAIN.SUBCLASS (e.g., AUTH.INVALID_TOKEN)
    These codes are stable and can be used for client-side error handling.
    """

    # Authentication & Authorization
    AUTH_INVALID_TOKEN = "AUTH.INVALID_TOKEN"
    AUTH_FORBIDDEN = "AUTH.FORBIDDEN"

    # API & Request
    API_BAD_REQUEST = "API.BAD_REQUEST"
    API_UNSUPPORTED = "API.UNSUPPORTED"
    API_RATE_LIMIT = "API.RATE_LIMIT"

    # Scanner
    SCAN_TIMEOUT = "SCAN.TIMEOUT"
    SCAN_NET_UNREACHABLE = "SCAN.NET_UNREACHABLE"
    SCAN_ADAPTER_DOWN = "SCAN.ADAPTER_DOWN"

    # Attack/Interference Engine
    ENGINE_ROOT_REQUIRED = "ENGINE.ROOT_REQUIRED"
    ENGINE_CAP_MISSING = "ENGINE.CAP_MISSING"
    ENGINE_RATE_LIMITED = "ENGINE.RATE_LIMITED"
    ENGINE_START_FAILED = "ENGINE.START_FAILED"

    # Dispatcher
    DISPATCH_CONFLICT_STATE = "DISPATCH.CONFLICT_STATE"
    DISPATCH_STRATEGY_NOT_ALLOWED = "DISPATCH.STRATEGY_NOT_ALLOWED"

    # Configuration
    CONFIG_VALIDATION = "CONFIG.VALIDATION"
    CONFIG_NOT_FOUND = "CONFIG.NOT_FOUND"
    CONFIG_LOCKED = "CONFIG.LOCKED"

    # Database
    DB_UNIQUE_VIOLATION = "DB.UNIQUE_VIOLATION"
    DB_DEADLOCKED = "DB.DEADLOCKED"

    # WebSocket
    WS_BAD_MESSAGE = "WS.BAD_MESSAGE"
    WS_PROTOCOL_ERROR = "WS.PROTOCOL_ERROR"

    # Internal
    INTERNAL_UNCAUGHT = "INTERNAL.UNCAUGHT"


# Mapping from error codes to HTTP status codes
_ERROR_CODE_TO_HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.AUTH_INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.API_BAD_REQUEST: status.HTTP_400_BAD_REQUEST,
    ErrorCode.API_UNSUPPORTED: status.HTTP_405_METHOD_NOT_ALLOWED,
    ErrorCode.API_RATE_LIMIT: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.SCAN_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
    ErrorCode.SCAN_NET_UNREACHABLE: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.SCAN_ADAPTER_DOWN: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.ENGINE_ROOT_REQUIRED: status.HTTP_403_FORBIDDEN,
    ErrorCode.ENGINE_CAP_MISSING: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.ENGINE_RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.ENGINE_START_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.DISPATCH_CONFLICT_STATE: status.HTTP_409_CONFLICT,
    ErrorCode.DISPATCH_STRATEGY_NOT_ALLOWED: status.HTTP_403_FORBIDDEN,
    ErrorCode.CONFIG_VALIDATION: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCode.CONFIG_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.CONFIG_LOCKED: status.HTTP_423_LOCKED,
    ErrorCode.DB_UNIQUE_VIOLATION: status.HTTP_409_CONFLICT,
    ErrorCode.DB_DEADLOCKED: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.WS_BAD_MESSAGE: status.HTTP_400_BAD_REQUEST,
    ErrorCode.WS_PROTOCOL_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.INTERNAL_UNCAUGHT: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


class AppError(Exception):
    """Base application exception with RFC 9457 Problem Details support.

    This exception class carries error metadata that will be serialized
    into a Problem Details JSON response following RFC 9457.

    Attributes:
        code: Stable error code (e.g., "AUTH.INVALID_TOKEN")
        http_status: HTTP status code (defaults based on code)
        detail: Human-readable error message
        type_uri: Machine-readable error type URI
        extra: Additional context (e.g., field validation errors)
    """

    def __init__(
        self,
        code: ErrorCode | str,
        detail: str = "",
        *,
        http_status: int | None = None,
        type_uri: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Initialize application error.

        Args:
            code: Error code (ErrorCode enum or string)
            detail: Human-readable error message
            http_status: HTTP status code (auto-mapped if None)
            type_uri: Problem Details type URI (auto-generated if None)
            extra: Additional context dictionary
        """
        super().__init__(detail)
        self.code = ErrorCode(code) if isinstance(code, str) else code
        self.detail = detail or self._default_detail()
        self.http_status = http_status or _ERROR_CODE_TO_HTTP_STATUS.get(
            self.code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.type_uri = type_uri or self._generate_type_uri()
        self.extra = extra or {}

    def _default_detail(self) -> str:
        """Generate default detail message from error code."""
        # Simple mapping for common cases
        defaults: dict[ErrorCode, str] = {
            ErrorCode.AUTH_INVALID_TOKEN: "Token is invalid or expired.",
            ErrorCode.AUTH_FORBIDDEN: (
                "You don't have permission to perform this action."
            ),
            ErrorCode.API_BAD_REQUEST: "Request parameters are invalid.",
            ErrorCode.API_RATE_LIMIT: "Rate limit exceeded. Please try again later.",
            ErrorCode.INTERNAL_UNCAUGHT: "An internal server error occurred.",
        }
        return defaults.get(self.code, "An error occurred.")

    def _generate_type_uri(self) -> str:
        """Generate Problem Details type URI from error code."""
        code_lower = self.code.value.lower().replace(".", "/").replace("_", "-")
        return f"https://zenethunter/errors/{code_lower}"

    def to_problem_details(self, instance: str | None = None) -> dict[str, Any]:
        """Convert to RFC 9457 Problem Details JSON structure.

        Args:
            instance: Optional instance URI (e.g., "/errors/{uuid}")

        Returns:
            Problem Details JSON object
        """
        result: dict[str, Any] = {
            "type": self.type_uri,
            "title": self._get_title(),
            "status": self.http_status,
            "detail": self.detail,
            "code": self.code.value,
        }
        if instance:
            result["instance"] = instance
        if self.extra:
            result.update(self.extra)
        return result

    def _get_title(self) -> str:
        """Get human-readable title from HTTP status."""
        status_names: dict[int, str] = {
            status.HTTP_400_BAD_REQUEST: "Bad Request",
            status.HTTP_401_UNAUTHORIZED: "Unauthorized",
            status.HTTP_403_FORBIDDEN: "Forbidden",
            status.HTTP_404_NOT_FOUND: "Not Found",
            status.HTTP_405_METHOD_NOT_ALLOWED: "Method Not Allowed",
            status.HTTP_409_CONFLICT: "Conflict",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "Unprocessable Entity",
            status.HTTP_423_LOCKED: "Locked",
            status.HTTP_429_TOO_MANY_REQUESTS: "Too Many Requests",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
            status.HTTP_502_BAD_GATEWAY: "Bad Gateway",
            status.HTTP_503_SERVICE_UNAVAILABLE: "Service Unavailable",
            status.HTTP_504_GATEWAY_TIMEOUT: "Gateway Timeout",
        }
        return status_names.get(self.http_status, "Error")
