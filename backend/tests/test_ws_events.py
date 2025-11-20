from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ws_events_device_added():
    # Connect to WS
    with client.websocket_connect("/api/ws") as websocket:
        # Trigger device add via API
        device_data = {
            "mac": "11:22:33:44:55:66",
            "ip": "10.0.0.10",
            "name": "New Device",
            "type": "mobile",
            "status": "online",
        }
        client.post("/api/devices", json=device_data)

        # Expect event
        data = websocket.receive_json()
        assert data["event"] == "deviceAdded"
        assert data["data"]["mac"] == device_data["mac"]


def test_ws_events_device_status_changed():
    # Add device first
    device_data = {
        "mac": "AA:BB:CC:DD:EE:FF",
        "ip": "10.0.0.11",
        "name": "Status Device",
        "type": "pc",
        "status": "online",
    }
    client.post("/api/devices", json=device_data)

    with client.websocket_connect("/api/ws") as websocket:
        # Update status
        device_data["status"] = "offline"
        client.post("/api/devices", json=device_data)

        # Expect event
        data = websocket.receive_json()
        assert data["event"] == "deviceStatusChanged"
        assert data["data"]["status"] == "offline"


def test_ws_events_log_added():
    with client.websocket_connect("/api/ws") as websocket:
        # Trigger log add via API
        log_data = {
            "level": "INFO",
            "module": "test",
            "message": "Test Log Event",
        }
        client.post("/api/logs", json=log_data)

        # Expect event
        data = websocket.receive_json()
        assert data["event"] == "logAdded"
        assert data["data"]["message"] == "Test Log Event"
