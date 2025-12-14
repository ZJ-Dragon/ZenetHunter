"""Event log repository for database operations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.event_log import EventLogLevelEnum, EventLogModel
from app.models.log import SystemLog


class EventLogRepository:
    """Repository for event log database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_log(
        self,
        level: str,
        module: str,
        message: str,
        correlation_id: str | None = None,
        device_mac: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Add event log entry.

        Args:
            level: Log level (debug, info, warning, error, critical)
            module: Module/component name
            message: Log message
            correlation_id: Optional correlation ID for request tracing
            device_mac: Optional device MAC address
            context: Optional additional context (will be stored as JSON)
        """
        try:
            log_level = EventLogLevelEnum(level.lower())
        except ValueError:
            log_level = EventLogLevelEnum.INFO

        context_json = None
        if context:
            context_json = json.dumps(context)

        model = EventLogModel(
            timestamp=datetime.now(UTC),
            level=log_level,
            module=module,
            message=message,
            correlation_id=correlation_id,
            device_mac=device_mac.lower() if device_mac else None,
            context=context_json,
        )
        self.session.add(model)
        await self.session.flush()

    async def get_logs(
        self,
        limit: int = 100,
        module: str | None = None,
        device_mac: str | None = None,
        level: str | None = None,
    ) -> list[SystemLog]:
        """Get recent event logs.

        Args:
            limit: Maximum number of logs to return
            module: Filter by module (optional)
            device_mac: Filter by device MAC (optional)
            level: Filter by log level (optional)

        Returns:
            List of SystemLog models, sorted by timestamp (newest first)
        """
        query = select(EventLogModel).order_by(desc(EventLogModel.timestamp))

        if module:
            query = query.where(EventLogModel.module == module)
        if device_mac:
            query = query.where(EventLogModel.device_mac == device_mac.lower())
        if level:
            try:
                log_level = EventLogLevelEnum(level.lower())
                query = query.where(EventLogModel.level == log_level)
            except ValueError:
                pass

        query = query.limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()

        logs = []
        for model in models:
            context = None
            if model.context:
                try:
                    context = json.loads(model.context)
                except (json.JSONDecodeError, TypeError):
                    pass

            logs.append(
                SystemLog(
                    id=None,  # ORM model doesn't expose UUID, use None
                    timestamp=model.timestamp,
                    level=model.level.value,
                    module=model.module,
                    message=model.message,
                    correlation_id=model.correlation_id,
                    device_mac=model.device_mac,
                    context=context,
                )
            )

        return logs


# Dependency injection for FastAPI
async def get_event_log_repository(session: AsyncSession) -> EventLogRepository:
    """Get event log repository instance."""
    return EventLogRepository(session)
