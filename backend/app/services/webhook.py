from __future__ import annotations

import logging
from typing import Any

from app.models.webhook import WebhookEventType
from app.services.state import get_state_manager

logger = logging.getLogger(__name__)


class WebhookService:
    """Handle incoming webhook events and apply side effects."""

    def __init__(self) -> None:
        self.state = get_state_manager()

    async def handle(self, event: dict[str, Any]) -> None:
        etype = event.get("type")
        data = event.get("data") or {}
        if etype == WebhookEventType.DEVICE_ONLINE.value:
            mac = data.get("mac")
            ip = data.get("ip")
            vendor = data.get("vendor")
            if mac:
                # Create or update device in state as online (best-effort)
                if hasattr(self.state, "upsert_device"):
                    self.state.upsert_device(mac=mac, ip=ip, vendor=vendor)
                if hasattr(self.state, "mark_device_online"):
                    self.state.mark_device_online(mac)
                logger.info("Webhook: device online %s %s", mac, ip or "")
        elif etype == WebhookEventType.POLICY_SWITCHED.value:
            mac = data.get("mac")
            to_policy = data.get("to_policy")
            if mac and to_policy:
                # Minimal side effect: store policy on device metadata (best-effort)
                if hasattr(self.state, "update_device_policy"):
                    self.state.update_device_policy(mac, to_policy)
                logger.info("Webhook: policy switched %s -> %s", mac, to_policy)
        else:
            logger.warning("Webhook: unknown event type %s", etype)


def get_webhook_service() -> WebhookService:
    return WebhookService()
