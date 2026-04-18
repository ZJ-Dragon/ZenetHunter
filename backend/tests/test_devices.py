import asyncio

from fastapi.testclient import TestClient

from app.core.database import get_session_factory
from app.repositories.device import DeviceRepository
from app.repositories.device_fingerprint import DeviceFingerprintRepository
from app.services.fingerprint_key import generate_fingerprint_key


def test_list_devices_empty(client: TestClient, reset_state):
    # Clear all devices from database before test
    # Note: TestClient uses sync API, so we use asyncio.run for async cleanup
    async def clear_db():
        session_factory = get_session_factory()
        async with session_factory() as session:
            repo = DeviceRepository(session)
            await repo.clear_all()
            await session.commit()

    asyncio.run(clear_db())

    response = client.get("/api/devices")
    assert response.status_code == 200
    assert response.json() == []


def test_add_and_get_device(client: TestClient):
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
    assert response.json()["attack_status"] == "idle"

    # Get device list
    response = client.get("/api/devices")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["mac"] == device_data["mac"]
    assert response.json()[0]["attack_status"] == "idle"

    # Get specific device
    response = client.get(f"/api/devices/{device_data['mac']}")
    assert response.status_code == 200
    assert response.json()["mac"] == device_data["mac"]


def test_get_nonexistent_device(client: TestClient):
    response = client.get("/api/devices/FF:FF:FF:FF:FF:FF")
    assert response.status_code == 404


def test_patch_device_updates_alias_and_tags(
    client: TestClient, admin_headers, reset_state
):
    device_data = {
        "mac": "00:11:22:33:44:56",
        "ip": "192.168.1.101",
        "name": "Patch Target",
        "type": "pc",
        "status": "online",
    }
    client.post("/api/devices", json=device_data)

    response = client.patch(
        f"/api/devices/{device_data['mac']}",
        json={"alias": "Desk PC", "tags": ["workstation", "trusted"]},
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["alias"] == "Desk PC"
    assert payload["tags"] == ["workstation", "trusted"]
    assert payload["display_name"] == "Desk PC"


def test_override_recognition_updates_vendor_model_and_type(
    client: TestClient, admin_headers, reset_state
):
    device_data = {
        "mac": "00:11:22:33:44:57",
        "ip": "192.168.1.102",
        "name": "Unknown Device",
        "type": "unknown",
        "status": "online",
    }
    client.post("/api/devices", json=device_data)

    response = client.post(
        f"/api/devices/{device_data['mac']}/recognition/override",
        json={"vendor": "Acme", "model": "SensorBox", "device_type": "iot"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["vendor"] == "Acme"
    assert payload["model"] == "SensorBox"
    assert payload["type"] == "iot"
    assert payload["recognition_confidence"] == 100
    assert payload["display_name"] == "Unknown Device"
    assert payload["display_vendor"] == "Acme"


def test_manual_label_uses_persisted_fingerprint_for_matching_key(
    client: TestClient, admin_headers, reset_state
):
    device_data = {
        "mac": "00:11:22:33:44:58",
        "ip": "192.168.1.103",
        "name": "Fingerprint Source",
        "type": "unknown",
        "status": "online",
    }
    client.post("/api/devices", json=device_data)

    fingerprint_data = {
        "dhcp_opt60_vci": "android-dhcp-14",
        "dhcp_opt12_hostname": "sensor-node-12",
        "user_agent": "Android",
    }

    async def seed_fingerprint():
        session_factory = get_session_factory()
        async with session_factory() as session:
            await DeviceFingerprintRepository(session).upsert(
                device_data["mac"], fingerprint_data
            )
            await session.commit()

    asyncio.run(seed_fingerprint())

    expected_key, _ = generate_fingerprint_key(
        fingerprint_data=fingerprint_data,
        mac=device_data["mac"],
        vendor_guess=None,
        model_guess=None,
    )

    response = client.put(
        f"/api/devices/{device_data['mac']}/manual-label",
        json={"name_manual": "Lab Sensor", "vendor_manual": "Acme"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fingerprint_key"] == expected_key
    assert payload["device"]["display_name"] == "Lab Sensor"
    assert payload["device"]["display_vendor"] == "Acme"
