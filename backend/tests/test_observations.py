"""Tests for probe observations API and repository."""

import pytest

pytest.importorskip("httpx", reason="httpx is required for FastAPI TestClient")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import get_session_factory  # noqa: E402
from app.repositories.probe_observation import ProbeObservationRepository  # noqa: E402


def _seed_observation(mac: str = "aa:bb:cc:dd:ee:ff", scan_run_id: str = "test-scan"):
    session_factory = get_session_factory()

    async def _inner():
        async with session_factory() as session:
            repo = ProbeObservationRepository(session)
            await repo.add(
                device_mac=mac,
                scan_run_id=scan_run_id,
                protocol="mdns",
                key_fields={"http_title": "Demo", "protocol": "mdns"},
                keywords=["demo"],
                keyword_hits=[],
                raw_summary="mdns Demo",
                redaction_level="standard",
            )
            await session.commit()

    import asyncio

    asyncio.run(_inner())


def test_device_observations_endpoint_returns_data(client: TestClient):
    _seed_observation()
    resp = client.get("/api/devices/aa:bb:cc:dd:ee:ff/observations?limit=5")
    assert resp.status_code == 200
    payload = resp.json()
    assert "items" in payload
    assert payload["total"] >= 1
    assert payload["items"][0]["protocol"] == "mdns"


def test_device_observations_ndjson_export(client: TestClient):
    _seed_observation(mac="11:22:33:44:55:66", scan_run_id="scan-123")
    resp = client.get(
        "/api/devices/11:22:33:44:55:66/observations",
        params={"format": "ndjson", "limit": 2},
    )
    assert resp.status_code == 200
    body = resp.text.strip()
    assert body.startswith("{") and body.endswith("}")
    assert "scan-123" in body
