from fastapi.testclient import TestClient


def test_config_lists(client: TestClient, admin_headers):
    mac = "11:22:33:44:55:66"

    # Initial state empty
    response = client.get("/api/config/lists")
    assert response.status_code == 200
    assert response.json()["allow_list"] == []
    assert response.json()["block_list"] == []

    # Add to allow list
    response = client.post(
        "/api/config/lists/allow", json={"mac": mac}, headers=admin_headers
    )
    assert response.status_code == 204

    response = client.get("/api/config/lists")
    assert mac in response.json()["allow_list"]

    # Move to block list
    response = client.post(
        "/api/config/lists/block", json={"mac": mac}, headers=admin_headers
    )
    assert response.status_code == 204

    response = client.get("/api/config/lists")
    assert mac not in response.json()["allow_list"]
    assert mac in response.json()["block_list"]

    # Remove from lists
    response = client.delete(f"/api/config/lists/{mac}", headers=admin_headers)
    assert response.status_code == 204

    response = client.get("/api/config/lists")
    assert mac not in response.json()["allow_list"]
    assert mac not in response.json()["block_list"]
