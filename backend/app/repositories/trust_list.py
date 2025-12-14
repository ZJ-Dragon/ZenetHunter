"""Trust list repository for database operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.trust_list import TrustListModel, TrustListTypeEnum


class TrustListRepository:
    """Repository for trust list (allow/block) database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_allow_list(self) -> list[str]:
        """Get all MAC addresses in allow list.

        Returns:
            List of MAC addresses (normalized to lowercase)
        """
        result = await self.session.execute(
            select(TrustListModel.mac).where(
                TrustListModel.list_type == TrustListTypeEnum.ALLOW
            )
        )
        return [row[0] for row in result.all()]

    async def get_block_list(self) -> list[str]:
        """Get all MAC addresses in block list.

        Returns:
            List of MAC addresses (normalized to lowercase)
        """
        result = await self.session.execute(
            select(TrustListModel.mac).where(
                TrustListModel.list_type == TrustListTypeEnum.BLOCK
            )
        )
        return [row[0] for row in result.all()]

    async def add_to_allow_list(self, mac: str, notes: str | None = None) -> None:
        """Add MAC address to allow list.

        Args:
            mac: MAC address (will be normalized to lowercase)
            notes: Optional notes
        """
        mac_lower = mac.lower()
        # Remove from block list if present
        await self.remove_from_block_list(mac_lower)

        # Check if already in allow list
        result = await self.session.execute(
            select(TrustListModel).where(
                TrustListModel.mac == mac_lower,
                TrustListModel.list_type == TrustListTypeEnum.ALLOW,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            model = TrustListModel(mac=mac_lower, list_type=TrustListTypeEnum.ALLOW, notes=notes)
            self.session.add(model)
            await self.session.flush()

    async def add_to_block_list(self, mac: str, notes: str | None = None) -> None:
        """Add MAC address to block list.

        Args:
            mac: MAC address (will be normalized to lowercase)
            notes: Optional notes
        """
        mac_lower = mac.lower()
        # Remove from allow list if present
        await self.remove_from_allow_list(mac_lower)

        # Check if already in block list
        result = await self.session.execute(
            select(TrustListModel).where(
                TrustListModel.mac == mac_lower,
                TrustListModel.list_type == TrustListTypeEnum.BLOCK,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            model = TrustListModel(mac=mac_lower, list_type=TrustListTypeEnum.BLOCK, notes=notes)
            self.session.add(model)
            await self.session.flush()

    async def remove_from_allow_list(self, mac: str) -> None:
        """Remove MAC address from allow list.

        Args:
            mac: MAC address (will be normalized to lowercase)
        """
        mac_lower = mac.lower()
        result = await self.session.execute(
            select(TrustListModel).where(
                TrustListModel.mac == mac_lower,
                TrustListModel.list_type == TrustListTypeEnum.ALLOW,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def remove_from_block_list(self, mac: str) -> None:
        """Remove MAC address from block list.

        Args:
            mac: MAC address (will be normalized to lowercase)
        """
        mac_lower = mac.lower()
        result = await self.session.execute(
            select(TrustListModel).where(
                TrustListModel.mac == mac_lower,
                TrustListModel.list_type == TrustListTypeEnum.BLOCK,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def remove_from_all_lists(self, mac: str) -> None:
        """Remove MAC address from both allow and block lists.

        Args:
            mac: MAC address (will be normalized to lowercase)
        """
        mac_lower = mac.lower()
        result = await self.session.execute(
            select(TrustListModel).where(TrustListModel.mac == mac_lower)
        )
        models = result.scalars().all()
        for model in models:
            await self.session.delete(model)
        await self.session.flush()


# Dependency injection for FastAPI
async def get_trust_list_repository(session: AsyncSession) -> TrustListRepository:
    """Get trust list repository instance."""
    return TrustListRepository(session)
