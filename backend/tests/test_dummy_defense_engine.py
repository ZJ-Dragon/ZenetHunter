"""Tests for dummy defense engine."""

import pytest

from app.core.engine.dummy_defense import DummyDefenseEngine
from app.models.defender import DefenseType


def test_check_capabilities():
    """Test check_capabilities always returns True."""
    engine = DummyDefenseEngine()
    assert engine.check_capabilities() is True


@pytest.mark.asyncio
async def test_apply_policy():
    """Test apply_policy logs correctly."""
    engine = DummyDefenseEngine()
    # Should complete without error
    await engine.apply_policy("00:11:22:33:44:55", DefenseType.BLOCK_WAN)
    await engine.apply_policy("00:11:22:33:44:55", DefenseType.QUARANTINE, {"param": "value"})


@pytest.mark.asyncio
async def test_remove_policy():
    """Test remove_policy logs correctly."""
    engine = DummyDefenseEngine()
    # Should complete without error
    await engine.remove_policy("00:11:22:33:44:55", DefenseType.BLOCK_WAN)


@pytest.mark.asyncio
async def test_enable_global_protection_syn_proxy():
    """Test enable_global_protection for SYN_PROXY."""
    engine = DummyDefenseEngine()
    await engine.enable_global_protection(DefenseType.SYN_PROXY)
    # Should complete without error


@pytest.mark.asyncio
async def test_enable_global_protection_udp_rate_limit():
    """Test enable_global_protection for UDP_RATE_LIMIT."""
    engine = DummyDefenseEngine()
    await engine.enable_global_protection(DefenseType.UDP_RATE_LIMIT)
    # Should complete without error


@pytest.mark.asyncio
async def test_enable_global_protection_tcp_reset():
    """Test enable_global_protection for TCP_RESET_POLICY."""
    engine = DummyDefenseEngine()
    await engine.enable_global_protection(DefenseType.TCP_RESET_POLICY)
    # Should complete without error


@pytest.mark.asyncio
async def test_enable_global_protection_walled_garden():
    """Test enable_global_protection for WALLED_GARDEN."""
    engine = DummyDefenseEngine()
    await engine.enable_global_protection(DefenseType.WALLED_GARDEN)
    # Should complete without error


@pytest.mark.asyncio
async def test_enable_global_protection_tarpit():
    """Test enable_global_protection for TARPIT."""
    engine = DummyDefenseEngine()
    await engine.enable_global_protection(DefenseType.TARPIT)
    # Should complete without error


@pytest.mark.asyncio
async def test_enable_global_protection_other():
    """Test enable_global_protection for other policies."""
    engine = DummyDefenseEngine()
    await engine.enable_global_protection(DefenseType.BLOCK_WAN)
    # Should complete without error (logs but doesn't match specific cases)


@pytest.mark.asyncio
async def test_disable_global_protection():
    """Test disable_global_protection."""
    engine = DummyDefenseEngine()
    await engine.disable_global_protection(DefenseType.SYN_PROXY)
    # Should complete without error
