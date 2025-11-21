from fastapi.testclient import TestClient

from app.models.defender import DefenseStatus, DefenseType
from app.models.device import Device, DeviceType


def test_get_policies(client: TestClient):
    response = client.get("/api/defense/policies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any(p["id"] == DefenseType.QUARANTINE for p in data)
    assert any(p["id"] == DefenseType.BLOCK_WAN for p in data)


def test_apply_defense_device_not_found(client: TestClient):
    response = client.post(
        "/api/devices/00:00:00:00:00:00/defense/apply",
        json={"policy": DefenseType.BLOCK_WAN},
    )
    assert response.status_code == 404


def test_apply_and_stop_defense(client: TestClient):
    # 1. Create a dummy device
    mac = "00:11:22:33:44:55"
    device_data = {
        "mac": mac,
        "ip": "192.168.1.100",
        "name": "Test Device",
        "type": "pc",
        "status": "online",
    }
    client.post("/api/devices", json=device_data)

    # 2. Apply defense
    response = client.post(
        f"/api/devices/{mac}/defense/apply",
        json={"policy": DefenseType.BLOCK_WAN},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["device_mac"] == mac
    assert data["status"] == DefenseStatus.ACTIVE
    assert data["active_policy"] == DefenseType.BLOCK_WAN

    # 3. Verify state updated
    dev_response = client.get(f"/api/devices/{mac}")
    assert dev_response.status_code == 200
    dev_data = dev_response.json()
    assert dev_data["defense_status"] == DefenseStatus.ACTIVE
    assert dev_data["active_defense_policy"] == DefenseType.BLOCK_WAN

    # 4. Stop defense
    stop_response = client.post(f"/api/devices/{mac}/defense/stop")
    assert stop_response.status_code == 200
    stop_data = stop_response.json()
    assert stop_data["status"] == DefenseStatus.INACTIVE

    # 5. Verify state updated again
    dev_response = client.get(f"/api/devices/{mac}")
    assert dev_response.json()["defense_status"] == DefenseStatus.INACTIVE
    assert dev_response.json()["active_defense_policy"] is None

