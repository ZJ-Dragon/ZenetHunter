import pytest
from unittest.mock import MagicMock
from app.core.engine.linux_defense import LinuxDefenseEngine
from app.models.defender import DefenseType

@pytest.mark.asyncio
async def test_linux_defense_walled_garden():
    engine = LinuxDefenseEngine()
    
    from asyncio import Future
    
    f = Future()
    f.set_result((0, "ok", ""))
    engine._run_cmd = MagicMock(return_value=f)
    
    await engine.enable_global_protection(DefenseType.WALLED_GARDEN)
    
    # Verify iptables calls were made
    # We expect 4 calls (Portal allow, DNS allow, HTTP redirect, HTTPS redirect)
    assert engine._run_cmd.call_count == 4
    call_args = engine._run_cmd.call_args_list
    
    # Check Portal allow rule
    portal_cmd = call_args[0][0][0]
    assert "iptables" in portal_cmd
    assert "FORWARD" in portal_cmd
    assert "192.168.1.1" in portal_cmd
    
    # Check HTTP redirect
    http_cmd = call_args[2][0][0]
    assert "nat" in http_cmd
    assert "PREROUTING" in http_cmd
    assert "80" in http_cmd
    assert "DNAT" in http_cmd
    
    # Check HTTPS redirect
    https_cmd = call_args[3][0][0]
    assert "443" in https_cmd

@pytest.mark.asyncio
async def test_linux_defense_walled_garden_disable():
    engine = LinuxDefenseEngine()
    
    from asyncio import Future
    
    f = Future()
    f.set_result((0, "ok", ""))
    engine._run_cmd = MagicMock(return_value=f)
    
    await engine.disable_global_protection(DefenseType.WALLED_GARDEN)
    
    # Verify deletion commands
    assert engine._run_cmd.call_count == 4

