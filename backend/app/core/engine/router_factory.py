"""Factory for creating RouterManager adapters based on settings."""

import logging

from app.core.config import get_settings
from app.core.engine.base_router import RouterManager
from app.core.engine.dummy_router import DummyRouterManager
from app.core.engine.xiaomi_router import XiaomiRouterManager

logger = logging.getLogger(__name__)


def get_router_manager() -> RouterManager:
    settings = get_settings()
    adapter = getattr(settings, "router_adapter", "dummy").lower()

    if adapter == "dummy":
        return DummyRouterManager()
    if adapter in {"xiaomi", "miwifi"}:
        return XiaomiRouterManager()

    logger.warning(
        "Unknown router adapter '%s'. Falling back to DummyRouterManager.", adapter
    )
    return DummyRouterManager()
