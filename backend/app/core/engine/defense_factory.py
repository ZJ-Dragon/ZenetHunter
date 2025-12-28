"""Factory for creating defense engine instances."""

import logging

from app.core.engine.base_defense import DefenseEngine
from app.core.engine.dummy_defense import DummyDefenseEngine
from app.core.engine.linux_defense import LinuxDefenseEngine
from app.core.platform.detect import (
    get_platform_features,
    is_linux,
    is_macos,
    is_windows,
)

logger = logging.getLogger(__name__)


def get_defense_engine() -> DefenseEngine:
    """
    Factory method to get the appropriate defense engine.
    Automatically detects platform and selects the appropriate engine.
    """
    platform_features = get_platform_features()
    is_root = platform_features.is_root

    # macOS defense engine
    if is_macos():
        if is_root and platform_features.has_pfctl:
            try:
                from app.core.engine.macos_defense import MacOSDefenseEngine

                logger.info(
                    "Root permissions on macOS detected. Using MacOSDefenseEngine."
                )
                return MacOSDefenseEngine()
            except ImportError as e:
                logger.warning(f"Failed to import MacOSDefenseEngine: {e}")
        else:
            reason = (
                "Root permissions missing" if not is_root else "pfctl not available"
            )
            logger.warning(
                f"{reason} on macOS (Platform: {platform_features.platform.value}). "
                "Falling back to DummyDefenseEngine. "
                "Defense capabilities will be simulated."
            )
        return DummyDefenseEngine()

    # Linux defense engine
    if is_linux():
        if is_root:
            logger.info("Root permissions on Linux detected. Using LinuxDefenseEngine.")
            return LinuxDefenseEngine()
        else:
            logger.warning(
                "Root permissions missing on Linux. "
                "Falling back to DummyDefenseEngine. "
                "Defense capabilities will be simulated."
            )
        return DummyDefenseEngine()

    # Windows defense engine
    if is_windows():
        if is_root and platform_features.has_netsh:
            try:
                from app.core.engine.windows_defense import WindowsDefenseEngine

                logger.info(
                    "Admin permissions on Windows detected. Using WindowsDefenseEngine."
                )
                return WindowsDefenseEngine()
            except ImportError as e:
                logger.warning(f"Failed to import WindowsDefenseEngine: {e}")
        else:
            reason = (
                "Admin permissions missing" if not is_root else "netsh not available"
            )
            logger.warning(
                f"{reason} on Windows (Platform: {platform_features.platform.value}). "
                "Falling back to DummyDefenseEngine. "
                "Defense capabilities will be simulated."
            )
        return DummyDefenseEngine()

    # Default fallback
    logger.warning(
        f"Unsupported platform: {platform_features.platform.value}. "
        "Falling back to DummyDefenseEngine. "
        "Defense capabilities will be simulated."
    )
    return DummyDefenseEngine()
