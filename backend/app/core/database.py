"""Database connection and session management.

This module provides SQLAlchemy database connection, session management,
and database initialization. Supports both SQLite (default) and PostgreSQL.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
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
    from pathlib import Path

    # Get absolute path to data directory
    # __file__ is backend/app/core/database.py, so:
    # parent = backend/app/core
    # parent.parent = backend/app
    # parent.parent.parent = backend
    backend_dir = Path(__file__).parent.parent.parent  # backend/app/core -> backend
    data_dir = backend_dir / "data"

    # Create directory with proper permissions
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        # Ensure directory is writable
        os.chmod(data_dir, 0o755)
    except OSError as e:
        logger.warning(
            f"Failed to create data directory {data_dir}: {e}. Using current directory."
        )
        data_dir = Path.cwd() / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

    # Use absolute path for SQLite to avoid path issues
    db_path = data_dir / "zenethunter.db"
    # SQLite URL: use absolute path with 4 slashes
    # (3 for protocol + 1 for absolute path)
    # aiosqlite requires absolute paths to be specified with 4 slashes
    abs_path = str(db_path.absolute())
    return f"sqlite+aiosqlite:///{abs_path}"


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
        # Prepare connection args with timeout for PostgreSQL
        # (asyncpg uses 'timeout' not 'connect_timeout')
        elif url.startswith("postgresql") or url.startswith("postgres"):
            connect_args = {
                "timeout": 10,  # Connection timeout in seconds for asyncpg
                "server_settings": {"application_name": "zenethunter_backend"},
            }

        _engine = create_async_engine(
            url,
            echo=False,  # Set to True for SQL debugging
            connect_args=connect_args,
            pool_pre_ping=True,  # Verify connections before using (reconnect if stale)
            pool_size=5,  # Connection pool size
            max_overflow=10,  # Max overflow connections
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_reset_on_return="commit",  # Reset connection state on return
        )
        logger.info(
            f"Database engine created: {url.split('@')[-1] if '@' in url else url}"
        )
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
    """Initialize database: create all tables and migrate schema if needed.

    This should be called on application startup.
    """
    try:
        # Import all models to ensure they are registered with Base.metadata
        from app.models.db import (  # noqa: F401
            DeviceModel,
            EventLogModel,
            TrustListModel,
        )
    except ImportError as e:
        logger.error(f"Failed to import database models: {e}")
        raise

    try:
        engine = get_engine()
        async with engine.begin() as conn:
            # Create all tables (if they don't exist)
            await conn.run_sync(Base.metadata.create_all)

            # Check if devices table exists and add model column if missing
            # This handles schema migration for existing databases
            db_url = get_database_url()
            if db_url.startswith("sqlite"):
                # For SQLite, check if model column exists
                try:
                    result = await conn.execute(
                        text(
                            "SELECT COUNT(*) as count FROM "
                            "pragma_table_info('devices') WHERE name = 'model'"
                        )
                    )
                    row = result.fetchone()
                    if row and row[0] == 0:
                        # Column doesn't exist, add it
                        logger.info(
                            "Adding 'model' column to devices table (migration)"
                        )
                        await conn.execute(
                            text(
                                "ALTER TABLE devices ADD COLUMN model VARCHAR(255) NULL"
                            )
                        )
                        await conn.commit()
                        logger.info(
                            "Migration completed: 'model' column added to devices table"
                        )
                except Exception as e:
                    # Table might not exist yet, which is fine
                    # create_all will handle it
                    logger.debug(
                        f"Could not check for model column "
                        f"(table may not exist yet): {e}"
                    )
            elif db_url.startswith("postgresql"):
                # For PostgreSQL, check if model column exists
                try:
                    result = await conn.execute(
                        text(
                            """
                            SELECT COUNT(*) as count
                            FROM information_schema.columns
                            WHERE table_name = 'devices' AND column_name = 'model'
                        """
                        )
                    )
                    row = result.fetchone()
                    if row and row[0] == 0:
                        # Column doesn't exist, add it
                        logger.info(
                            "Adding 'model' column to devices table (migration)"
                        )
                        await conn.execute(
                            text(
                                "ALTER TABLE devices ADD COLUMN model VARCHAR(255) NULL"
                            )
                        )
                        await conn.commit()
                        logger.info(
                            "Migration completed: 'model' column added to devices table"
                        )
                except Exception as e:
                    # Table might not exist yet, which is fine
                    # create_all will handle it
                    logger.debug(
                        f"Could not check for model column "
                        f"(table may not exist yet): {e}"
                    )

        logger.info("Database tables created/updated")
    except Exception as e:
        logger.error(f"Failed to create/update database tables: {e}", exc_info=True)
        raise


async def close_db() -> None:
    """Close database connections.

    This should be called on application shutdown.
    """
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")
