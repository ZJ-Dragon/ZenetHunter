from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_start_scan():
    # Start scan
    response = client.post("/api/scan/start", json={"type": "quick"})
    assert response.status_code == 202
    data = response.json()
    
    assert "id" in data
    assert data["status"] == "running"
    assert "started_at" in data


def test_start_scan_invalid_type():
    response = client.post("/api/scan/start", json={"type": "invalid"})
    assert response.status_code == 422


def test_websocket_connection():
    with client.websocket_connect("/api/ws") as websocket:
        # Connection established
        pass

