import pytest
from unittest.mock import MagicMock, patch
from app.core.engine.defense_factory import get_defense_engine
from app.core.engine.linux_defense import LinuxDefenseEngine
from app.models.defender import DefenseType

@pytest.mark.asyncio
async def test_linux_defense_tcp_reset():
    engine = LinuxDefenseEngine()
    
    from asyncio import Future
    
    f = Future()
    f.set_result((0, "ok", ""))
    engine._run_cmd = MagicMock(return_value=f)
    
    await engine.enable_global_protection(DefenseType.TCP_RESET_POLICY)
    
    # Verify iptables calls were made
    # We expect 2 calls (TCP and UDP rules)
    assert engine._run_cmd.call_count == 2
    call_args = engine._run_cmd.call_args_list
    
    # Check TCP rule
    tcp_cmd = call_args[0][0][0]
    assert "iptables" in tcp_cmd
    assert "tcp" in tcp_cmd
    assert "REJECT" in tcp_cmd
    assert "tcp-reset" in tcp_cmd
    
    # Check UDP rule
    udp_cmd = call_args[1][0][0]
    assert "udp" in udp_cmd
    assert "icmp-port-unreachable" in udp_cmd

@pytest.mark.asyncio
async def test_linux_defense_tcp_reset_disable():
    engine = LinuxDefenseEngine()
    
    from asyncio import Future
    
    f = Future()
    f.set_result((0, "ok", ""))
    engine._run_cmd = MagicMock(return_value=f)
    
    await engine.disable_global_protection(DefenseType.TCP_RESET_POLICY)
    
    # Verify deletion commands
    assert engine._run_cmd.call_count == 2

