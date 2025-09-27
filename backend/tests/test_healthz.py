

"""Minimal health check test: `/healthz` should return 200 and a small JSON body.

The test uses FastAPI's TestClient (which relies on `httpx`). If `httpx` is not
available in the environment, the test will be **skipped** with a clear reason.
"""

import pytest

# Skip test early if httpx (TestClient dependency) is missing
pytest.importorskip("httpx", reason="httpx is required for FastAPI TestClient")

from fastapi.testclient import TestClient  # noqa: E402  (import after skip)
from app.main import app  # noqa: E402


def test_healthz_ok():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
