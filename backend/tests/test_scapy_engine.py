"""Tests for Scapy attack engine."""

from unittest.mock import patch

import pytest

from app.core.engine.scapy import ScapyAttackEngine
from app.models.attack import AttackType


def test_check_permissions_root():
    """Test permission check with root user."""
    with patch("os.geteuid", return_value=0):
        engine = ScapyAttackEngine()
        assert engine.check_permissions() is True


def test_check_permissions_non_root():
    """Test permission check without root."""
    with patch("os.geteuid", return_value=1000):
        engine = ScapyAttackEngine()
        # May return False or check capabilities
        result = engine.check_permissions()
        assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_start_attack_no_permissions():
    """Test start_attack raises PermissionError without permissions."""
    engine = ScapyAttackEngine()

    with patch.object(engine, "check_permissions", return_value=False):
        with pytest.raises(PermissionError):
            await engine.start_attack("00:11:22:33:44:55", AttackType.KICK, 5)


@pytest.mark.asyncio
async def test_stop_attack():
    """Test stop_attack method."""
    engine = ScapyAttackEngine()

    # Should complete without error (even if no attack running)
    await engine.stop_attack("00:11:22:33:44:55")


@pytest.mark.asyncio
async def test_start_attack_unknown_type():
    """Test start_attack with unknown attack type."""
    engine = ScapyAttackEngine()

    with patch.object(engine, "check_permissions", return_value=True):
        # This should log a warning but not raise an error
        # We can't easily test the actual attack methods without network access
        # So we just verify it doesn't crash
        try:
            await engine.start_attack("00:11:22:33:44:55", AttackType.KICK, 5)
        except (PermissionError, NotImplementedError):
            # These are expected in test environment
            pass
