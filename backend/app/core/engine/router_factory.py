"""Factory for creating RouterManager adapters based on settings."""

import logging

from app.core.config import get_settings
from app.core.engine.base_router import RouterManager
from app.core.engine.dummy_router import DummyRouterManager

logger = logging.getLogger(__name__)


def get_router_manager() -> RouterManager:
    settings = get_settings()
    adapter = getattr(settings, "router_adapter", "dummy").lower()

    if adapter == "dummy":
        return DummyRouterManager()

    logger.warning(
        "Unknown router adapter '%s'. Falling back to DummyRouterManager.", adapter
    )
    return DummyRouterManager()
