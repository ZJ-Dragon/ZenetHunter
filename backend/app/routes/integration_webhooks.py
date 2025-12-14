from __future__ import annotations

import hmac
import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status

from app.core.config import get_settings
from app.core.exceptions import AppError, ErrorCode
from app.models.webhook import HEADER_SIGNATURE, HEADER_TIMESTAMP
from app.services.webhook import WebhookService, get_webhook_service


router = APIRouter(tags=["integration", "webhooks"])


def _sign(secret: str, timestamp: str, raw_body: bytes) -> str:
    msg = (timestamp + ".").encode("utf-8") + raw_body
    mac = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return f"sha256={mac}"


@router.post(
    "/integration/webhooks",
    status_code=status.HTTP_200_OK,
)
async def receive_webhook(
    request: Request,
    zh_timestamp: Annotated[str | None, Header(alias=HEADER_TIMESTAMP)] = None,
    zh_signature: Annotated[str | None, Header(alias=HEADER_SIGNATURE)] = None,
    service: WebhookService = Depends(get_webhook_service),
):
    """Receive integration webhooks (device online / policy switched) with HMAC verification.

    Security:
    - Headers: X-ZH-Timestamp, X-ZH-Signature (sha256=<hex>)
    - Signature: HMAC-SHA256 over "{timestamp}.{raw_body}" using WEBHOOK_SECRET
    - Anti-replay: Reject if timestamp is older than tolerance window
    """
    if not zh_timestamp or not zh_signature:
        raise AppError(ErrorCode.AUTH_INVALID_TOKEN, "Missing webhook signature")

    settings = get_settings()
    try:
        ts = int(zh_timestamp)
    except Exception:
        raise AppError(ErrorCode.API_BAD_REQUEST, "Invalid timestamp header")

    now = int(datetime.now(UTC).timestamp())
    if abs(now - ts) > int(getattr(settings, "webhook_tolerance_sec", 300)):
        raise AppError(ErrorCode.AUTH_INVALID_TOKEN, "Timestamp outside tolerance")

    raw = await request.body()
    expected = _sign(settings.webhook_secret, zh_timestamp, raw)
    if not hmac.compare_digest(expected, zh_signature):
        raise AppError(ErrorCode.AUTH_INVALID_TOKEN, "Invalid signature")

    # Parse JSON and dispatch
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        raise AppError(ErrorCode.API_BAD_REQUEST, "Invalid JSON body")

    await service.handle(payload)
    return {"status": "ok"}
