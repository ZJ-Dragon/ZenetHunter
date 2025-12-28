"""Factory for creating attack engines based on environment."""

import logging

from app.core.engine.base import AttackEngine
from app.core.engine.dummy import DummyAttackEngine

logger = logging.getLogger(__name__)

# Try to import ScapyAttackEngine, but handle ImportError gracefully
try:
    from app.core.engine.scapy import ScapyAttackEngine

    SCAPY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ScapyAttackEngine not available: {e}. Using DummyAttackEngine.")
    SCAPY_AVAILABLE = False
    ScapyAttackEngine = None  # type: ignore


def get_attack_engine() -> AttackEngine:
    """
    Get the appropriate attack engine.

    Strategy:
    1. Try ScapyAttackEngine if available.
    2. Check permissions (root).
    3. If permitted, return Scapy engine.
    4. Else, fallback to DummyAttackEngine with a warning.
    """
    if SCAPY_AVAILABLE and ScapyAttackEngine is not None:
        try:
            scapy_engine = ScapyAttackEngine()
            if scapy_engine.check_permissions():
                logger.info("Using ScapyAttackEngine (Root permissions detected)")
                return scapy_engine
            else:
                logger.warning(
                    "Root permissions missing. Falling back to DummyAttackEngine. "
                    "Attacks will be simulated."
                )
        except Exception as e:
            logger.warning(
                f"Failed to initialize ScapyAttackEngine: {e}. Using DummyAttackEngine."
            )
    else:
        logger.info("Scapy not available. Using DummyAttackEngine for simulation.")

    return DummyAttackEngine()
