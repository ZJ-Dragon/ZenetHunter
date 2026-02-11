from fastapi.testclient import TestClient


def test_start_scan(client: TestClient, admin_headers):
    # Start scan
    response = client.post(
        "/api/scan/start", json={"type": "quick"}, headers=admin_headers
    )
    assert response.status_code == 202
    data = response.json()

    assert "id" in data
    assert data["status"] == "running"
    assert "started_at" in data


def test_start_scan_invalid_type(client: TestClient, admin_headers):
    response = client.post(
        "/api/scan/start", json={"type": "invalid"}, headers=admin_headers
    )
    assert response.status_code == 422


def test_websocket_connection(client: TestClient):
    with client.websocket_connect("/api/ws"):
        # Connection established
        pass
