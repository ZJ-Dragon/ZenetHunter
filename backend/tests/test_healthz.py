"""API skeleton tests: health check and OpenAPI documentation.

The tests use FastAPI's TestClient (which relies on `httpx`). If `httpx` is not
available in the environment, the tests will be **skipped** with a clear reason.
"""

import pytest

# Skip test early if httpx (TestClient dependency) is missing
pytest.importorskip("httpx", reason="httpx is required for FastAPI TestClient")

from fastapi.testclient import TestClient  # noqa: E402  (import after skip)

from app.main import app  # noqa: E402


def test_healthz_ok():
    """Test that /healthz endpoint returns 200 OK with correct JSON response."""
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_openapi_json_available():
    """Test that OpenAPI JSON schema is accessible."""
    from app.core.config import get_settings

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert "info" in data
    # Verify title matches settings (defaults to "ZenetHunter API")
    settings = get_settings()
    assert data["info"]["title"] == settings.app_name


def test_docs_available():
    """Test that Swagger UI documentation is accessible."""
    client = TestClient(app)
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_redoc_available():
    """Test that ReDoc documentation is accessible."""
    client = TestClient(app)
    resp = client.get("/redoc")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
