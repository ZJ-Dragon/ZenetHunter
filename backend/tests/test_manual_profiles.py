import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.repositories.device_manual_profile import DeviceManualProfileRepository


@pytest.mark.asyncio
async def test_manual_profile_match_prefers_fingerprint(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/manual.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        repo = DeviceManualProfileRepository(session)
        await repo.upsert(
            fingerprint_key="abc123",
            manual_name="Manual Name",
            manual_vendor="Manual Vendor",
            match_keys={"oui": "aabbcc"},
            mac="aa:bb:cc:dd:ee:ff",
        )
        await repo.upsert(
            fingerprint_key="zzz999",
            manual_name="MAC Match",
            manual_vendor="Vendor MAC",
            match_keys={"oui": "deadbe"},
            mac="de:ad:be:ef:00:01",
        )
        await session.commit()

    async with session_factory() as session:
        repo = DeviceManualProfileRepository(session)
        exact = await repo.find_best_match(
            fingerprint_key="abc123", mac=None, match_keys={"oui": "ffff"}
        )
        mac_match = await repo.find_best_match(
            fingerprint_key="nomatch", mac="de:ad:be:ef:00:01", match_keys={}
        )

    assert exact is not None
    assert exact.manual_name == "Manual Name"
    assert mac_match is not None
    assert mac_match.manual_vendor == "Vendor MAC"
