"""Repository for user accounts."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.user_account import UserAccountModel


class UserAccountRepository:
    """CRUD operations for user accounts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> UserAccountModel | None:
        result = await self.session.execute(
            select(UserAccountModel).where(UserAccountModel.username == username)
        )
        return result.scalar_one_or_none()

    async def create_admin(
        self, username: str, password_hash: str, is_builtin: bool = False
    ) -> UserAccountModel:
        model = UserAccountModel(
            username=username,
            password_hash=password_hash,
            role="admin",
            is_builtin=is_builtin,
        )
        self.session.add(model)
        await self.session.flush()
        return model

    async def has_admin(self) -> bool:
        result = await self.session.execute(
            select(UserAccountModel.username).where(UserAccountModel.role == "admin")
        )
        return result.first() is not None
