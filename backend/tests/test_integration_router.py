from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_rate_limit_apply_and_remove(admin_headers):
    mac = "AA:BB:CC:DD:EE:FF"

    # Apply
    resp = client.post(
        "/api/integration/router/rate-limit",
        json={"target_mac": mac, "up_kbps": 1000, "down_kbps": 2000},
        headers=admin_headers,
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "success"

    # Remove
    resp = client.delete(
        f"/api/integration/router/rate-limit/{mac}", headers=admin_headers
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "success"


def test_rate_limit_validation(admin_headers):
    mac = "11:22:33:44:55:66"
    # Neither up nor down provided -> 422
    resp = client.post(
        "/api/integration/router/rate-limit",
        json={"target_mac": mac},
        headers=admin_headers,
    )
    assert resp.status_code == 422


def test_acl_apply_and_remove(admin_headers):
    # Apply deny tcp 80 from any to 192.168.1.0/24
    resp = client.post(
        "/api/integration/router/acl",
        json={
            "src": "any",
            "dst": "192.168.1.0/24",
            "proto": "tcp",
            "port": "80",
            "action": "deny",
            "priority": 10,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "success"
    assert "rule_id" in data.get("data", {})
    rule_id = data["data"]["rule_id"]

    # Remove
    resp = client.delete(f"/api/integration/router/acl/{rule_id}", headers=admin_headers)
    assert resp.status_code == 202
    assert resp.json()["status"] == "success"


def test_isolation_and_reintegrate(admin_headers):
    mac = "22:33:44:55:66:77"
    # Isolation with guest VLAN requires vlan_id
    resp = client.post(
        "/api/integration/router/isolate",
        json={"target_mac": mac, "mode": "guest_vlan", "vlan_id": 100},
        headers=admin_headers,
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "success"

    # Reintegrate
    resp = client.post(
        f"/api/integration/router/reintegrate/{mac}", headers=admin_headers
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "success"


def test_isolation_validation(admin_headers):
    mac = "33:44:55:66:77:88"
    # Missing vlan_id for guest_vlan -> 422
    resp = client.post(
        "/api/integration/router/isolate",
        json={"target_mac": mac, "mode": "guest_vlan"},
        headers=admin_headers,
    )
    assert resp.status_code == 422
