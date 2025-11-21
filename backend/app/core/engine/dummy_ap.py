"""Dummy implementation of Access Point Manager for testing."""

import logging
from typing import Any

from app.core.engine.base_ap import AccessPointManager
from app.models.wpa3 import Wpa3Config

logger = logging.getLogger(__name__)


class DummyAccessPointManager(AccessPointManager):
    """Safe, log-only AP manager for non-hardware environments."""

    async def check_capabilities(self) -> bool:
        """Always returns True for dummy manager."""
        return True

    async def configure_wpa3(
        self, config: Wpa3Config, params: dict[str, Any] | None = None
    ) -> bool:
        logger.info(
            f"[DummyAP] Configuring WPA3: mode={config.mode}, "
            f"SSID={config.ssid}, RADIUS={config.radius is not None}"
        )
        return True

    async def assign_vlan(
        self, mac: str, vlan_id: int, port: str | None = None
    ) -> bool:
        logger.info(f"[DummyAP] Assigning {mac} to VLAN {vlan_id} (port: {port})")
        return True

    async def remove_vlan_assignment(self, mac: str) -> bool:
        logger.info(f"[DummyAP] Removing VLAN assignment for {mac}")
        return True

