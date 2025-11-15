"""Tests for error handling middleware.

Tests verify that middleware correctly handles exceptions, generates
correlation IDs, and returns RFC 9457 Problem Details responses.
"""

import pytest

pytest.importorskip("httpx", reason="httpx is required for FastAPI TestClient")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.exceptions import AppError, ErrorCode  # noqa: E402
from app.main import app  # noqa: E402


def test_middleware_correlation_id_header():
    """Test middleware adds correlation_id to response headers."""
    client = TestClient(app)
    response = client.get("/healthz")
    assert "X-Correlation-Id" in response.headers
    assert response.headers["X-Correlation-Id"]  # Not empty


def test_middleware_custom_correlation_id():
    """Test middleware uses X-Correlation-Id from request header."""
    client = TestClient(app)
    custom_id = "test-correlation-123"
    response = client.get("/healthz", headers={"X-Correlation-Id": custom_id})
    assert response.headers["X-Correlation-Id"] == custom_id


def test_middleware_app_error_handling():
    """Test middleware handles AppError and returns Problem Details."""

    # Create a test endpoint that raises AppError
    @app.get("/test-error")
    async def test_error_endpoint():
        raise AppError(ErrorCode.AUTH_INVALID_TOKEN, detail="Test error")

    client = TestClient(app)
    response = client.get("/test-error")

    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "https://zenethunter/errors/auth/invalid-token"
    assert data["status"] == 401
    assert data["detail"] == "Test error"
    assert data["code"] == "AUTH.INVALID_TOKEN"
    assert "correlation_id" in data
    assert "X-Correlation-Id" in response.headers


def test_middleware_uncaught_exception():
    """Test middleware handles uncaught exceptions."""

    # Create a test endpoint that raises unexpected exception
    @app.get("/test-uncaught")
    async def test_uncaught_endpoint():
        raise ValueError("Unexpected error")

    client = TestClient(app)
    response = client.get("/test-uncaught")

    assert response.status_code == 500
    data = response.json()
    assert data["code"] == "INTERNAL.UNCAUGHT"
    assert data["status"] == 500
    assert "correlation_id" in data
    assert "X-Correlation-Id" in response.headers


def test_middleware_problem_details_structure():
    """Test Problem Details response follows RFC 9457 structure."""

    @app.get("/test-problem")
    async def test_problem_endpoint():
        raise AppError(
            ErrorCode.API_BAD_REQUEST,
            detail="Invalid request",
            extra={"field": "param", "hint": "Check documentation"},
        )

    client = TestClient(app)
    response = client.get("/test-problem")

    data = response.json()
    # Required RFC 9457 fields
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    # Custom fields
    assert "code" in data
    assert "correlation_id" in data
    assert "instance" in data
    # Extra context
    assert data["field"] == "param"
    assert data["hint"] == "Check documentation"
