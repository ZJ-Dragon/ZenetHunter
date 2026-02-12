"""Local-only reset of volatile device data.

Clears devices and related runtime tables while preserving long-lived manual profiles.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from sqlalchemy import delete, func, select

from app.core.database import get_database_url, get_session_factory, init_db
from app.models.db import (
    DeviceFingerprintModel,
    DeviceModel,
    EventLogModel,
    ManualOverrideModel,
    ProbeObservationModel,
)
from app.repositories.event_log import EventLogRepository

ALLOWED_ENVS = {"development"}


async def reset_runtime_data() -> dict[str, Any]:
    """Clear volatile device data; keep manual profile library intact."""
    app_env = os.getenv("APP_ENV", "development")
    if app_env not in ALLOWED_ENVS:
        raise RuntimeError(f"Reset is only allowed in {ALLOWED_ENVS}, got {app_env}")

    await init_db()

    session_factory = get_session_factory()
    async with session_factory() as session:
        counts: dict[str, int] = {}
        targets = [
            ProbeObservationModel,
            DeviceFingerprintModel,
            ManualOverrideModel,
            DeviceModel,
        ]

        # Count existing rows
        for model in targets:
            result = await session.execute(
                select(func.count()).select_from(model)  # type: ignore[arg-type]
            )
            counts[model.__tablename__] = int(result.scalar_one() or 0)

        # Delete rows in dependency-safe order (children first)
        for model in targets:
            await session.execute(delete(model))

        # Preserve manual profiles and event logs, but record the reset action
        event_repo = EventLogRepository(session)
        await event_repo.add_log(
            level="INFO",
            module="maintenance",
            message="Local runtime data reset",
            context={
                "database_url": get_database_url(),
                "removed_rows": counts,
                "preserved_tables": [
                    "device_manual_profiles",
                    EventLogModel.__tablename__,
                ],
            },
        )
        await session.commit()

    return counts


def main() -> None:
    counts = asyncio.run(reset_runtime_data())
    removed = ", ".join(f"{table}: {count}" for table, count in counts.items())
    print(f"[reset-runtime] removed rows -> {removed or 'none'}")
    print("[reset-runtime] device_manual_profiles preserved")


if __name__ == "__main__":
    main()
