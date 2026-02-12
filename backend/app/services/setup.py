"""Setup/OOBE service."""

import logging

from app.core.database import get_session_factory
from app.models.auth import UserRole
from app.repositories.app_setting import AppSettingRepository
from app.repositories.user_account import UserAccountRepository
from app.services.auth import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)

FIRST_RUN_KEY = "first_run_completed"


class SetupService:
    """Manage first-run bootstrap and acknowledgements."""

    def __init__(self):
        self.session_factory = get_session_factory()

    async def get_status(self) -> dict[str, bool]:
        async with self.session_factory() as session:
            settings_repo = AppSettingRepository(session)
            user_repo = UserAccountRepository(session)
            admin_exists = await user_repo.has_admin()
            first_run_completed = await settings_repo.get_bool(
                FIRST_RUN_KEY, default=False
            )
            return {
                "admin_exists": admin_exists,
                "first_run_completed": first_run_completed,
            }

    async def register_admin(self, username: str, password: str) -> str:
        """Register first admin; returns access token."""
        async with self.session_factory() as session:
            settings_repo = AppSettingRepository(session)
            user_repo = UserAccountRepository(session)

            if await user_repo.has_admin():
                raise ValueError("Admin already exists")

            password_hash = hash_password(password)
            await user_repo.create_admin(username=username, password_hash=password_hash)
            await session.commit()

            token = create_access_token(data={"sub": username, "role": UserRole.ADMIN})
            return token

    async def acknowledge_disclaimer(self, username: str) -> None:
        """Mark first-run completed after disclaimer acknowledgement."""
        async with self.session_factory() as session:
            settings_repo = AppSettingRepository(session)
            await settings_repo.set_bool(FIRST_RUN_KEY, True)
            await session.commit()
            logger.info("First-run disclaimer acknowledged by %s", username)

    async def authenticate(self, username: str, password: str) -> str | None:
        """Validate credentials and return token on success."""
        async with self.session_factory() as session:
            user_repo = UserAccountRepository(session)
            user = await user_repo.get_by_username(username)
            if not user:
                return None
            if not verify_password(password, user.password_hash):
                return None

            return create_access_token(data={"sub": username, "role": user.role})
