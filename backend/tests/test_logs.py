from fastapi.testclient import TestClient


def test_logs_api(client: TestClient):
    # Test empty logs
    response = client.get("/api/logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Add a log
    log_data = {"level": "INFO", "module": "test_module", "message": "Test log message"}
    response = client.post("/api/logs", json=log_data)
    assert response.status_code == 201

    # Verify log is present
    response = client.get("/api/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 1
    assert logs[-1]["message"] == "Test log message"
