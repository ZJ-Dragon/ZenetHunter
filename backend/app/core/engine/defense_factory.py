"""Factory for creating defense engine instances."""

import logging
import os

from app.core.engine.base_defense import DefenseEngine
from app.core.engine.dummy_defense import DummyDefenseEngine
from app.core.engine.linux_defense import LinuxDefenseEngine

logger = logging.getLogger(__name__)


def get_defense_engine() -> DefenseEngine:
    """
    Factory method to get the appropriate defense engine.
    Returns LinuxDefenseEngine if root, else DummyDefenseEngine.
    """
    try:
        is_root = os.geteuid() == 0
    except AttributeError:
        # Windows or non-POSIX
        is_root = False

    if is_root:
        logger.info("Root permissions detected. Using LinuxDefenseEngine.")
        return LinuxDefenseEngine()
    else:
        logger.warning(
            "Root permissions missing. Falling back to DummyDefenseEngine. "
            "Defense capabilities will be simulated."
        )
        return DummyDefenseEngine()
