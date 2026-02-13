"""Reset / Replay service to wipe volatile data and restart OOBE."""

import logging

from sqlalchemy import delete

from app.core.database import get_session_factory
from app.models.db.app_setting import AppSettingModel
from app.models.db.device import DeviceModel
from app.models.db.device_fingerprint import DeviceFingerprintModel
from app.models.db.manual_override import ManualOverrideModel
from app.models.db.probe_observation import ProbeObservationModel
from app.models.db.user_account import UserAccountModel
from app.repositories.app_setting import AppSettingRepository
from app.repositories.event_log import EventLogRepository

logger = logging.getLogger(__name__)

FIRST_RUN_KEY = "first_run_completed"


class ResetService:
    """Provides a deterministic replay/reset routine."""

    def __init__(self):
        self.session_factory = get_session_factory()

    async def replay(self) -> None:
        """Reset volatile state and OOBE flags."""
        async with self.session_factory() as session:
            log_repo = EventLogRepository(session)
            settings_repo = AppSettingRepository(session)

            # Clear runtime/volatile data
            await session.execute(delete(ProbeObservationModel))
            await session.execute(delete(DeviceFingerprintModel))
            await session.execute(delete(ManualOverrideModel))
            await session.execute(delete(DeviceModel))

            # Reset app settings and OOBE state
            await session.execute(delete(AppSettingModel))
            await settings_repo.set_bool(FIRST_RUN_KEY, False)

            # Remove all user accounts to force re-registration
            await session.execute(delete(UserAccountModel))

            # Audit log
            await log_repo.add_log(
                level="info",
                module="reset",
                message="replay_triggered",
                context={"action": "replay"},
            )

            await session.commit()
            logger.info("Replay/reset completed successfully")
