"""Manual profile matching should bind to MAC/IP/fingerprint, not vendor-only."""

import asyncio

from app.core.database import get_session_factory
from app.repositories.device_manual_profile import DeviceManualProfileRepository


def test_manual_profile_requires_strong_keys():
    session_factory = get_session_factory()

    async def _inner():
        async with session_factory() as session:
            repo = DeviceManualProfileRepository(session)
            # Seed a profile bound to a specific MAC and fingerprint
            await repo.upsert(
                fingerprint_key="fp-strong",
                manual_name="router",
                manual_vendor="Xiaomi",
                match_keys={"mdns_services": ["_http._tcp"]},
                mac="aa:bb:cc:dd:ee:ff",
                ip_hint="192.168.1.10",
                keywords=[],
            )
            await session.commit()

            # Matching with the same MAC succeeds
            same_mac = await repo.find_best_match(
                fingerprint_key=None,
                mac="aa:bb:cc:dd:ee:ff",
                match_keys={"mdns_services": ["_http._tcp"]},
                ip_hint="192.168.1.10",
            )
            assert same_mac is not None
            assert same_mac.manual_name == "router"

            # Different MAC but exact fingerprint key still matches (intended reuse)
            fp_match = await repo.find_best_match(
                fingerprint_key="fp-strong",
                mac="11:22:33:44:55:66",
                match_keys={},
                ip_hint=None,
            )
            assert fp_match is not None

            # Different MAC + no fingerprint match should NOT match on vendor-only hints
            no_match = await repo.find_best_match(
                fingerprint_key=None,
                mac="11:22:33:44:55:66",
                match_keys={"mdns_services": ["_http._tcp"]},
                ip_hint="192.168.1.20",
            )
            assert no_match is None

    asyncio.run(_inner())
