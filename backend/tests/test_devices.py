from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_devices_empty():
    response = client.get("/api/devices")
    assert response.status_code == 200
    assert response.json() == []


def test_add_and_get_device():
    device_data = {
        "mac": "00:11:22:33:44:55",
        "ip": "192.168.1.100",
        "name": "Test Device",
        "type": "pc",
        "status": "online",
    }

    # Add device
    response = client.post("/api/devices", json=device_data)
    assert response.status_code == 200
    assert response.json()["mac"] == device_data["mac"]

    # Get device list
    response = client.get("/api/devices")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["mac"] == device_data["mac"]

    # Get specific device
    response = client.get(f"/api/devices/{device_data['mac']}")
    assert response.status_code == 200
    assert response.json()["mac"] == device_data["mac"]


def test_get_nonexistent_device():
    response = client.get("/api/devices/FF:FF:FF:FF:FF:FF")
    assert response.status_code == 404
