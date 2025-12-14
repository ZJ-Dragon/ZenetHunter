from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_problem_details_validation(admin_headers):
    # Missing required vlan_id for guest_vlan triggers validation
    r = client.post(
        "/api/integration/router/isolate",
        json={"target_mac": "00:11:22:33:44:55", "mode": "guest_vlan"},
        headers=admin_headers,
    )
    assert r.status_code == 422
    body = r.json()
    # RFC9457 problem fields
    assert set(["type", "title", "status", "detail", "code"]).issubset(body)
    assert body["code"] == "CONFIG.VALIDATION"
    assert "correlation_id" in body


def test_ws_error_envelope_on_bad_message():
    with client.websocket_connect("/api/ws") as ws:
        # Send invalid (non-JSON) message to trigger WS.BAD_MESSAGE
        ws.send_text("not-json")
        msg = ws.receive_json()
        assert msg.get("event") == "error"
        assert msg.get("code") == "WS.BAD_MESSAGE"
        assert "correlation_id" in msg
