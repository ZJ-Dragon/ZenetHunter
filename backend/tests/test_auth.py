from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import create_access_token

client = TestClient(app)


def get_admin_token():
    return create_access_token(data={"sub": "admin", "role": "admin"})


def get_guest_token():
    return create_access_token(data={"sub": "guest", "role": "guest"})


def test_login_success():
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "zenethunter"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure():
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_protected_route_admin():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    # Try starting a scan
    response = client.post("/api/scan/start", json={"type": "quick"}, headers=headers)
    # Should succeed (202) or fail validation (422), but not 401/403
    assert response.status_code == 202


def test_protected_route_guest():
    token = get_guest_token()
    headers = {"Authorization": f"Bearer {token}"}
    # Try starting a scan - should fail with 403 (guest not allowed)
    response = client.post("/api/scan/start", json={"type": "quick"}, headers=headers)
    # Guest token -> Admin check fails -> 403
    assert response.status_code == 403


def test_protected_route_no_token():
    # Try starting a scan without header
    response = client.post("/api/scan/start", json={"type": "quick"})
    # No token -> guest -> admin check fails -> 403
    assert response.status_code == 403
