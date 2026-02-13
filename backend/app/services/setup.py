"""Setup/OOBE service."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.database import get_engine, get_session_factory
from app.models.auth import UserRole
from app.repositories.app_setting import AppSettingRepository
from app.repositories.user_account import UserAccountRepository
from app.services.auth import create_access_token

logger = logging.getLogger(__name__)

FIRST_RUN_KEY = "first_run_completed"
PBKDF2_ITERATIONS = 100_000


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

    def hash_password(self, password: str, salt: str | None = None) -> tuple[str, str]:
        """Hash password using PBKDF2-SHA256 with provided or random salt."""
        salt_bytes = bytes.fromhex(salt) if salt else secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt_bytes, PBKDF2_ITERATIONS
        )
        hash_hex = derived.hex()
        salt_hex = salt_bytes.hex()
        stored = f"pbkdf2${PBKDF2_ITERATIONS}${salt_hex}${hash_hex}"
        return stored, salt_hex

    def verify_password(self, stored_hash: str, password: str) -> bool:
        """Verify password against stored PBKDF2 hash format."""
        try:
            prefix, iterations_str, salt_hex, hash_hex = stored_hash.split("$", 3)
            if prefix != "pbkdf2":
                return False
            iterations = int(iterations_str)
            salt_bytes = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
            candidate = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt_bytes, iterations
            )
            return hmac.compare_digest(candidate, expected)
        except Exception:
            return False

    async def register_admin(self, username: str, password: str) -> str:
        """Register first admin; returns access token."""
        username_clean = username.strip()
        if not username_clean or username_clean.lower() == "admin":
            raise ValueError(
                "Username 'admin' is reserved for the limited debug account"
            )
        async with self.session_factory() as session:
            user_repo = UserAccountRepository(session)

            if await user_repo.has_admin():
                raise ValueError("Admin already exists")

            password_hash, _ = self.hash_password(password)
            try:
                await user_repo.create_admin(
                    username=username_clean,
                    password_hash=password_hash,
                    is_builtin=False,
                )
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                message = str(exc)
                logger.warning("Failed to create admin: %s", message)
                if "user_accounts.id" in message and "NOT NULL" in message:
                    await self._rebuild_user_accounts_table()
                    # retry once after rebuild
                    async with self.session_factory() as retry_session:
                        retry_repo = UserAccountRepository(retry_session)
                        await retry_repo.create_admin(
                            username=username_clean,
                            password_hash=password_hash,
                            is_builtin=False,
                        )
                        await retry_session.commit()
                else:
                    raise ValueError("Username already exists") from None

            token = create_access_token(
                data={"sub": username_clean, "role": UserRole.ADMIN}
            )
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
            try:
                user = await user_repo.get_by_username(username)
            except OperationalError as exc:
                # Gracefully handle partially migrated schemas during tests/first run
                logger.warning(
                    "User lookup failed; falling back to built-in admin: %s", exc
                )
                user = None

            if user and self.verify_password(user.password_hash, password):
                return create_access_token(
                    data={
                        "sub": username,
                        "role": user.role,
                        "limited_admin": user.is_builtin,
                    }
                )

            if username == "admin" and password == "zenethunter":
                return create_access_token(
                    data={
                        "sub": username,
                        "role": UserRole.ADMIN,
                        "limited_admin": True,
                    }
                )

            return None

    async def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials from database."""
        async with self.session_factory() as session:
            user_repo = UserAccountRepository(session)
            user = await user_repo.get_by_username(username)
            if not user:
                return False
            return self.verify_password(user.password_hash, password)

    async def _rebuild_user_accounts_table(self) -> None:
        """Recreate user_accounts with autoincrement id if schema is legacy."""
        engine = get_engine()
        db_url = str(engine.url)
        if not db_url.startswith("sqlite"):
            return
        logger.warning("Rebuilding legacy user_accounts table (sqlite)")
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS user_accounts_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        username VARCHAR(100) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL DEFAULT 'admin',
                        is_builtin BOOLEAN NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    INSERT OR IGNORE INTO user_accounts_new
                    (username, password_hash, role, is_builtin, created_at, updated_at)
                    SELECT
                        username,
                        password_hash,
                        role,
                        COALESCE(is_builtin, 0),
                        COALESCE(created_at, CURRENT_TIMESTAMP),
                        COALESCE(updated_at, CURRENT_TIMESTAMP)
                    FROM user_accounts
                    """
                )
            )
            await conn.execute(text("DROP TABLE IF EXISTS user_accounts"))
            await conn.execute(
                text("ALTER TABLE user_accounts_new RENAME TO user_accounts")
            )
            await conn.commit()
        logger.info("user_accounts table rebuilt (sqlite)")
