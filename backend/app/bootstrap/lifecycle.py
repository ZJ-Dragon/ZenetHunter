"""Application lifecycle management."""

from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI

from app.core.database import close_db, get_database_url, init_db
from app.core.logging import setup_logging
from app.services.websocket import get_connection_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize lightweight resources at startup and clean them up on shutdown."""
    shutdown_event = asyncio.Event()

    def signal_handler(sig, _frame):
        logger.info("Received signal %s, initiating graceful shutdown...", sig)
        shutdown_event.set()

    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except ValueError:
        logger.warning("Cannot register signal handlers (not in main thread)")

    setup_logging()
    app.state.start_time = datetime.now(UTC)
    app.state.shutdown_event = shutdown_event

    max_retries = 5
    retry_delay = 2
    db_url = get_database_url()
    safe_url = db_url.split("@")[-1] if "@" in db_url else db_url

    for attempt in range(max_retries):
        try:
            logger.info(
                "Initializing database connection (attempt %s/%s) to %s",
                attempt + 1,
                max_retries,
                safe_url,
            )
            await init_db()
            logger.info("Database initialized successfully")
            break
        except Exception as exc:
            error_type = type(exc).__name__
            if attempt < max_retries - 1:
                logger.warning(
                    "Database initialization failed (attempt %s/%s): %s: %s. "
                    "Retrying in %ss...",
                    attempt + 1,
                    max_retries,
                    error_type,
                    exc,
                    retry_delay,
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    "Database initialization failed after %s attempts. Error: %s: %s",
                    max_retries,
                    error_type,
                    exc,
                )
                raise

    try:
        yield
    finally:
        logger.info("Application shutdown initiated, cleaning up resources...")
        shutdown_timeout = 5.0
        try:
            async with asyncio.timeout(shutdown_timeout):
                await _cancel_background_tasks()
                await _close_websockets()
                await _close_database()
        except TimeoutError:
            logger.error(
                "Shutdown exceeded %ss timeout, forcing immediate exit",
                shutdown_timeout,
            )
        except Exception as exc:
            logger.error("Unexpected error during shutdown: %s", exc, exc_info=True)
        finally:
            logger.info("Shutdown complete")


async def _cancel_background_tasks() -> None:
    logger.info("Step 1/3: Cancelling active background tasks...")
    tasks_to_cancel: list[asyncio.Task] = []
    try:
        for task in asyncio.all_tasks():
            if task is asyncio.current_task() or task.done():
                continue
            task_name = task.get_name()
            if any(
                keyword in task_name.lower()
                for keyword in ["scan", "attack", "operation", "defense"]
            ):
                logger.debug("Cancelling task: %s", task_name)
                task.cancel()
                tasks_to_cancel.append(task)
        if tasks_to_cancel:
            logger.info("Waiting for %s tasks to cancel...", len(tasks_to_cancel))
            await asyncio.wait(tasks_to_cancel, timeout=1.0)
            logger.info("Background tasks cancelled")
    except Exception as exc:
        logger.warning("Error cancelling background tasks: %s", exc)


async def _close_websockets() -> None:
    logger.info("Step 2/3: Closing WebSocket connections...")
    try:
        ws_manager = get_connection_manager()
        await asyncio.wait_for(ws_manager.close_all(), timeout=1.0)
        logger.info("WebSocket connections closed")
    except TimeoutError:
        logger.warning("WebSocket close timed out, forcing shutdown")
    except Exception as exc:
        logger.warning("Error closing WebSocket connections: %s", exc)


async def _close_database() -> None:
    logger.info("Step 3/3: Closing database connections...")
    try:
        await asyncio.wait_for(close_db(), timeout=1.0)
        logger.info("Database connections closed")
    except TimeoutError:
        logger.warning("Database close timed out, forcing shutdown")
    except Exception as exc:
        logger.warning("Error closing database: %s", exc)
