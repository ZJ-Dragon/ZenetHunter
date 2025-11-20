"""Factory for creating attack engines based on environment."""

import logging

from app.core.engine.base import AttackEngine
from app.core.engine.dummy import DummyAttackEngine
from app.core.engine.scapy import ScapyAttackEngine

logger = logging.getLogger(__name__)


def get_attack_engine() -> AttackEngine:
    """
    Get the appropriate attack engine.
    
    Strategy:
    1. Try ScapyAttackEngine.
    2. Check permissions (root).
    3. If permitted, return Scapy engine.
    4. Else, fallback to DummyAttackEngine with a warning.
    """
    scapy_engine = ScapyAttackEngine()
    if scapy_engine.check_permissions():
        logger.info("Using ScapyAttackEngine (Root permissions detected)")
        return scapy_engine
    
    logger.warning(
        "Root permissions missing. Falling back to DummyAttackEngine. "
        "Attacks will be simulated."
    )
    return DummyAttackEngine()

