"""Repository for application settings."""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.app_setting import AppSettingModel


class AppSettingRepository:
    """Simple key/value settings storage."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> str | None:
        result = await self.session.execute(
            select(AppSettingModel).where(AppSettingModel.key == key)
        )
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def set(self, key: str, value: str) -> None:
        result = await self.session.execute(
            select(AppSettingModel).where(AppSettingModel.key == key)
        )
        model = result.scalar_one_or_none()
        if model:
            model.value = value
        else:
            self.session.add(AppSettingModel(key=key, value=value))
        await self.session.flush()

    async def get_bool(self, key: str, default: bool = False) -> bool:
        raw = await self.get(key)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except Exception:
            return default

    async def set_bool(self, key: str, value: bool) -> None:
        await self.set(key, json.dumps(bool(value)))
