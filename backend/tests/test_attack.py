from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_attack_lifecycle(admin_headers):
    # 1. Create a device
    device_data = {
        "mac": "AA:BB:CC:DD:EE:FF",
        "ip": "10.0.0.5",
        "name": "Target Device",
        "type": "mobile",
        "status": "online",
    }
    client.post("/api/devices", json=device_data)

    # 2. Start Attack
    attack_req = {"type": "kick", "duration": 5}
    response = client.post(
        f"/api/devices/{device_data['mac']}/attack",
        json=attack_req,
        headers=admin_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "running"
    assert data["device_mac"] == device_data["mac"]

    # 3. Check device status in state
    response = client.get(f"/api/devices/{device_data['mac']}")
    assert response.json()["attack_status"] == "running"

    # 4. Stop Attack
    response = client.post(
        f"/api/devices/{device_data['mac']}/attack/stop", headers=admin_headers
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "stopped"

    # 5. Check device status in state
    response = client.get(f"/api/devices/{device_data['mac']}")
    assert response.json()["attack_status"] == "stopped"


def test_attack_nonexistent_device(admin_headers):
    response = client.post(
        "/api/devices/FF:FF:FF:FF:FF:FF/attack",
        json={"type": "kick"},
        headers=admin_headers,
    )
    # Service returns success=False -> Router raises 400
    assert response.status_code == 400


def test_stop_attack_nonexistent_device(admin_headers):
    response = client.post(
        "/api/devices/FF:FF:FF:FF:FF:FF/attack/stop", headers=admin_headers
    )
    # Service returns success=False -> Router raises 404
    assert response.status_code == 404
