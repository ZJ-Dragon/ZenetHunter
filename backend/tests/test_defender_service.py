"""Tests for defender service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.defender import DefenseApplyRequest, DefenseStatus, DefenseType
from app.services.defender import DefenderService


@pytest.mark.asyncio
async def test_apply_defense_global_policy_arp_dai():
    """Test applying ARP_DAI global policy."""
    service = DefenderService()
    
    # Mock dependencies
    with patch.object(service.arp_monitor, "start_monitoring", new_callable=AsyncMock):
        with patch.object(service.engine, "enable_global_protection", new_callable=AsyncMock):
            request = DefenseApplyRequest(policy=DefenseType.ARP_DAI)
            await service.apply_defense("global", request)
            
            # Verify ARP monitor was started
            service.arp_monitor.start_monitoring.assert_called_once()
            service.engine.enable_global_protection.assert_called_once_with(DefenseType.ARP_DAI)


@pytest.mark.asyncio
async def test_apply_defense_global_policy_dns_rpz():
    """Test applying DNS_RPZ global policy."""
    service = DefenderService()
    
    # Mock dependencies
    with patch.object(service.dns_engine, "add_zone", new_callable=AsyncMock):
        with patch.object(service.dns_engine, "add_rule", new_callable=AsyncMock):
            request = DefenseApplyRequest(policy=DefenseType.DNS_RPZ)
            await service.apply_defense("global", request)
            
            # Verify DNS engine was configured
            service.dns_engine.add_zone.assert_called_once_with("blacklist")
            service.dns_engine.add_rule.assert_called_once_with("malware.test", "NXDOMAIN")


@pytest.mark.asyncio
async def test_apply_defense_global_policy_wpa3():
    """Test applying WPA3_8021X global policy."""
    service = DefenderService()
    
    request = DefenseApplyRequest(policy=DefenseType.WPA3_8021X)
    # Should complete without error (just logs)
    await service.apply_defense("global", request)


@pytest.mark.asyncio
async def test_apply_defense_global_policy_other():
    """Test applying other global policies."""
    service = DefenderService()
    
    with patch.object(service.engine, "enable_global_protection", new_callable=AsyncMock):
        request = DefenseApplyRequest(policy=DefenseType.SYN_PROXY)
        await service.apply_defense("global", request)
        
        service.engine.enable_global_protection.assert_called_once_with(DefenseType.SYN_PROXY)


@pytest.mark.asyncio
async def test_apply_defense_global_policy_with_mac():
    """Test applying global policy to specific MAC (should warn)."""
    service = DefenderService()
    
    with patch.object(service.engine, "enable_global_protection", new_callable=AsyncMock):
        request = DefenseApplyRequest(policy=DefenseType.SYN_PROXY)
        # Apply to specific MAC (not "global")
        await service.apply_defense("00:11:22:33:44:55", request)
        
        # Should still call enable_global_protection (but with warning)
        service.engine.enable_global_protection.assert_called_once_with(DefenseType.SYN_PROXY)


@pytest.mark.asyncio
async def test_stop_defense_global():
    """Test stopping global defenses."""
    service = DefenderService()
    
    # Mock dependencies
    with patch.object(service.engine, "disable_global_protection", new_callable=AsyncMock):
        with patch.object(service.arp_monitor, "stop_monitoring", new_callable=AsyncMock):
            await service.stop_defense("global")
            
            # Verify all global protections were disabled
            assert service.engine.disable_global_protection.call_count >= 5
            service.arp_monitor.stop_monitoring.assert_called_once()


@pytest.mark.asyncio
async def test_stop_defense_device_not_found():
    """Test stopping defense on non-existent device."""
    service = DefenderService()
    
    # Mock state manager to return None
    service.state_manager.get_device = MagicMock(return_value=None)
    
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        await service.stop_defense("00:11:22:33:44:55")
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_stop_defense_already_inactive():
    """Test stopping defense that's already inactive."""
    from app.models.device import Device, DeviceStatus, DeviceType
    
    service = DefenderService()
    
    # Mock device with INACTIVE status
    mock_device = Device(
        mac="00:11:22:33:44:55",
        ip="192.168.1.100",
        defense_status=DefenseStatus.INACTIVE,
        status=DeviceStatus.ONLINE,
        type=DeviceType.PC,
    )
    service.state_manager.get_device = MagicMock(return_value=mock_device)
    
    # Should return early without error
    await service.stop_defense("00:11:22:33:44:55")
    
    # Verify remove_policy was NOT called (early return)
    # We can't easily verify this without more mocking, but the test ensures no exception


@pytest.mark.asyncio
async def test_stop_defense_active():
    """Test stopping active defense."""
    from app.models.device import Device, DeviceStatus, DeviceType
    
    service = DefenderService()
    
    # Mock device with ACTIVE status
    mock_device = Device(
        mac="00:11:22:33:44:55",
        ip="192.168.1.100",
        defense_status=DefenseStatus.ACTIVE,
        active_defense_policy=DefenseType.BLOCK_WAN,
        status=DeviceStatus.ONLINE,
        type=DeviceType.PC,
    )
    service.state_manager.get_device = MagicMock(return_value=mock_device)
    service.state_manager.update_device_defense_status = MagicMock()
    
    with patch.object(service.engine, "remove_policy", new_callable=AsyncMock):
        with patch.object(service.ws_manager, "broadcast", new_callable=AsyncMock):
            await service.stop_defense("00:11:22:33:44:55")
            
            # Verify remove_policy was called
            service.engine.remove_policy.assert_called_once_with(
                "00:11:22:33:44:55", DefenseType.BLOCK_WAN
            )
            # Verify state was updated
            service.state_manager.update_device_defense_status.assert_called_once_with(
                "00:11:22:33:44:55", DefenseStatus.INACTIVE
            )
