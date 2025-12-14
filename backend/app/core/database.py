"""Database connection and session management.

This module provides SQLAlchemy database connection, session management,
and database initialization. Supports both SQLite (default) and PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()

# Global engine and session factory
_engine = None
_session_factory = None


def get_database_url() -> str:
    """Get database URL from settings, defaulting to SQLite.

    Returns:
        Database URL string (SQLite by default, PostgreSQL if DATABASE_URL is set)
    """
    settings = get_settings()
    if settings.database_url:
        # PostgreSQL URL (convert from sync to async driver)
        url = settings.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url
    # Default to SQLite (create data directory if needed)
    import os

    os.makedirs("./data", exist_ok=True)
    return "sqlite+aiosqlite:///./data/zenethunter.db"


def get_engine():
    """Get or create database engine (singleton).

    Returns:
        SQLAlchemy async engine
    """
    global _engine
    if _engine is None:
        url = get_database_url()
        # SQLite requires check_same_thread=False for async
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_async_engine(
            url,
            echo=False,  # Set to True for SQL debugging
            connect_args=connect_args,
            pool_pre_ping=True,  # Verify connections before using
        )
        logger.info(f"Database engine created: {url.split('@')[-1] if '@' in url else url}")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create session factory (singleton).

    Returns:
        SQLAlchemy async session factory
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session.

    Yields:
        Async database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database: create all tables.

    This should be called on application startup.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def close_db() -> None:
    """Close database connections.

    This should be called on application shutdown.
    """
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")
