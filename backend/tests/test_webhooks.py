import hmac
import hashlib
import json
import time

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


client = TestClient(app)


def _sign(secret: str, ts: int, body: bytes) -> str:
    msg = f"{ts}.".encode("utf-8") + body
    return "sha256=" + hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def test_webhook_valid_device_online():
    s = get_settings()
    ts = int(time.time())
    payload = {
        "id": "evt_1",
        "type": "device.online",
        "data": {"mac": "AA:BB:CC:DD:EE:FF", "ip": "192.168.1.10"},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign(s.webhook_secret, ts, body)

    r = client.post(
        "/api/integration/webhooks",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-ZH-Timestamp": str(ts),
            "X-ZH-Signature": sig,
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_webhook_invalid_signature():
    ts = int(time.time())
    body = json.dumps({"id": "evt_2", "type": "device.online", "data": {"mac": "11:22:33:44:55:66"}}).encode(
        "utf-8"
    )
    r = client.post(
        "/api/integration/webhooks",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-ZH-Timestamp": str(ts),
            "X-ZH-Signature": "sha256=deadbeef",
        },
    )
    assert r.status_code in (401, 403)


def test_webhook_stale_timestamp():
    s = get_settings()
    ts = int(time.time()) - (int(getattr(s, "webhook_tolerance_sec", 300)) + 10)
    body = json.dumps({"id": "evt_3", "type": "policy.switched", "data": {"mac": "aa", "to_policy": "guest"}}).encode(
        "utf-8"
    )
    sig = _sign(s.webhook_secret, ts, body)
    r = client.post(
        "/api/integration/webhooks",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-ZH-Timestamp": str(ts),
            "X-ZH-Signature": sig,
        },
    )
    assert r.status_code in (401, 403)
