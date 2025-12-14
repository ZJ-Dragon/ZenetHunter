import asyncio

import pytest

from app.core.engine.xiaomi_router import XiaomiRouterManager
from app.models.router_integration import (
    ACLAction,
    ACLRule,
    IsolationMode,
    IsolationPolicy,
    RateLimitPolicy,
)


@pytest.mark.asyncio
async def test_xiaomi_qos_rate_limit_mock_apply_remove():
    mgr = XiaomiRouterManager()  # no host configured -> mock mode
    policy = RateLimitPolicy(
        target_mac="AA:BB:CC:DD:EE:FF", up_kbps=500, down_kbps=1000, duration=1
    )

    ok_apply = await mgr.set_rate_limit(policy)
    assert ok_apply is True

    # Auto-revert after duration
    await asyncio.sleep(1.1)
    ok_remove = await mgr.remove_rate_limit(policy.target_mac)
    # remove should still return True even if already auto-cleared
    assert ok_remove is True


@pytest.mark.asyncio
async def test_xiaomi_qos_acl_noop_and_remove():
    mgr = XiaomiRouterManager()
    rule = ACLRule(
        src="any",
        dst="192.168.1.0/24",
        proto="tcp",
        port="80",
        action=ACLAction.DENY,
        priority=10,
    )
    rid = await mgr.apply_acl_rule(rule)
    assert isinstance(rid, str) and len(rid) > 0
    ok = await mgr.remove_acl_rule(rid)
    assert ok is True


@pytest.mark.asyncio
async def test_xiaomi_qos_isolation_mock_and_reintegrate():
    mgr = XiaomiRouterManager()
    iso = IsolationPolicy(
        target_mac="22:33:44:55:66:77",
        mode=IsolationMode.GUEST_VLAN,
        vlan_id=100,
        duration=1,
    )
    ok_iso = await mgr.isolate_device(iso)
    assert ok_iso is True
    # Wait auto-reintegrate
    await asyncio.sleep(1.1)
    ok_re = await mgr.reintegrate_device(iso.target_mac)
    assert ok_re is True
