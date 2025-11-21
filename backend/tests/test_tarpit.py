from unittest.mock import MagicMock

import pytest

from app.core.engine.linux_defense import LinuxDefenseEngine
from app.models.defender import DefenseType


@pytest.mark.asyncio
async def test_linux_defense_tarpit_check_module():
    engine = LinuxDefenseEngine()

    from asyncio import Future

    # Mock successful module check
    f = Future()
    f.set_result((0, "TARPIT target", ""))
    engine._run_cmd = MagicMock(return_value=f)

    result = await engine._check_tarpit_module()
    assert result is True

    # Mock failed module check
    f2 = Future()
    f2.set_result((1, "", "TARPIT: No such target"))
    engine._run_cmd = MagicMock(return_value=f2)

    result = await engine._check_tarpit_module()
    assert result is False


@pytest.mark.asyncio
async def test_linux_defense_tarpit_enable():
    engine = LinuxDefenseEngine()

    from asyncio import Future

    # Mock module check success
    check_f = Future()
    check_f.set_result((0, "TARPIT target", ""))

    # Mock iptables command success
    iptables_f = Future()
    iptables_f.set_result((0, "ok", ""))

    engine._run_cmd = MagicMock(side_effect=[check_f, iptables_f])

    await engine.enable_global_protection(DefenseType.TARPIT)

    # Verify iptables TARPIT command was called
    assert engine._run_cmd.call_count == 2
    call_args = engine._run_cmd.call_args_list

    # Check TARPIT rule
    tarpit_cmd = call_args[1][0][0]
    assert "iptables" in tarpit_cmd
    assert "tcp" in tarpit_cmd
    assert "TARPIT" in tarpit_cmd


@pytest.mark.asyncio
async def test_linux_defense_tarpit_disable():
    engine = LinuxDefenseEngine()

    from asyncio import Future

    f = Future()
    f.set_result((0, "ok", ""))
    engine._run_cmd = MagicMock(return_value=f)

    await engine.disable_global_protection(DefenseType.TARPIT)

    # Verify deletion command
    assert engine._run_cmd.call_count == 1
