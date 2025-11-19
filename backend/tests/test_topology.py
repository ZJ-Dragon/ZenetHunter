from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_topology_structure():
    # Add a device first to make topology interesting
    device_data = {
        "mac": "AA:BB:CC:DD:EE:FF",
        "ip": "10.0.0.1",
        "name": "Gateway Router",
        "type": "router",
        "status": "online"
    }
    client.post("/api/devices", json=device_data)
    
    response = client.get("/api/topology")
    assert response.status_code == 200
    data = response.json()
    
    assert "nodes" in data
    assert "links" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["links"], list)
    
    # Verify our device is in nodes
    found = False
    target_mac = device_data["mac"].lower()
    for node in data["nodes"]:
        if node["id"].lower() == target_mac:
            found = True
            break
    assert found

