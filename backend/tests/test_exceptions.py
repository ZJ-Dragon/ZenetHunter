"""Tests for application exceptions and error handling.

Tests verify that AppError produces correct Problem Details responses
and error codes map to appropriate HTTP status codes.
"""

from fastapi import status

from app.core.exceptions import AppError, ErrorCode


def test_app_error_basic():
    """Test basic AppError creation and attributes."""
    error = AppError(ErrorCode.AUTH_INVALID_TOKEN, detail="Token expired")
    assert error.code == ErrorCode.AUTH_INVALID_TOKEN
    assert error.detail == "Token expired"
    assert error.http_status == status.HTTP_401_UNAUTHORIZED
    assert "auth/invalid-token" in error.type_uri


def test_app_error_default_detail():
    """Test AppError uses default detail when not provided."""
    error = AppError(ErrorCode.AUTH_INVALID_TOKEN)
    assert error.detail == "Token is invalid or expired."


def test_app_error_problem_details():
    """Test AppError.to_problem_details() produces RFC 9457 structure."""
    error = AppError(ErrorCode.API_BAD_REQUEST, detail="Invalid parameter")
    problem = error.to_problem_details(instance="/errors/test-123")

    assert problem["type"] == error.type_uri
    assert problem["title"] == "Bad Request"
    assert problem["status"] == status.HTTP_400_BAD_REQUEST
    assert problem["detail"] == "Invalid parameter"
    assert problem["code"] == "API.BAD_REQUEST"
    assert problem["instance"] == "/errors/test-123"


def test_app_error_extra_context():
    """Test AppError includes extra context in problem details."""
    error = AppError(
        ErrorCode.CONFIG_VALIDATION,
        detail="Validation failed",
        extra={"field": "api_key", "reason": "missing"},
    )
    problem = error.to_problem_details()
    assert problem["field"] == "api_key"
    assert problem["reason"] == "missing"


def test_error_code_http_status_mapping():
    """Test error codes map to correct HTTP status codes."""
    test_cases = [
        (ErrorCode.AUTH_INVALID_TOKEN, status.HTTP_401_UNAUTHORIZED),
        (ErrorCode.AUTH_FORBIDDEN, status.HTTP_403_FORBIDDEN),
        (ErrorCode.API_BAD_REQUEST, status.HTTP_400_BAD_REQUEST),
        (ErrorCode.API_RATE_LIMIT, status.HTTP_429_TOO_MANY_REQUESTS),
        (ErrorCode.SCAN_TIMEOUT, status.HTTP_504_GATEWAY_TIMEOUT),
        (ErrorCode.ENGINE_ROOT_REQUIRED, status.HTTP_403_FORBIDDEN),
        (ErrorCode.DISPATCH_CONFLICT_STATE, status.HTTP_409_CONFLICT),
        (ErrorCode.CONFIG_VALIDATION, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (ErrorCode.DB_UNIQUE_VIOLATION, status.HTTP_409_CONFLICT),
        (ErrorCode.INTERNAL_UNCAUGHT, status.HTTP_500_INTERNAL_SERVER_ERROR),
    ]

    for error_code, expected_status in test_cases:
        error = AppError(error_code)
        assert (
            error.http_status == expected_status
        ), f"{error_code.value} should map to {expected_status}"
