"""Health check endpoints.

This module provides health probe endpoints for container orchestration
and monitoring systems (e.g., Kubernetes, Docker healthchecks).
"""

import asyncio
import logging
import os
import signal
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_admin
from app.models.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Kubernetes-style health probe endpoint.

    Returns:
        dict: A simple status response indicating the service is healthy.

    Example:
        GET /healthz -> 200 OK {"status": "ok"}
    """
    return {"status": "ok"}


@router.post("/shutdown", summary="Gracefully shutdown the application")
async def shutdown_application(
    current_user: Annotated[User, Depends(get_current_admin)],
) -> dict[str, str]:
    """Gracefully shutdown the backend application.

    This endpoint allows administrators to remotely trigger a graceful
    shutdown of the backend service. All active operations will be
    cancelled and resources will be properly cleaned up.

    ⚠️  ADMIN ONLY - Requires administrator authentication.

    Returns:
        dict: Shutdown initiation status

    Note:
        The shutdown happens asynchronously. The application will:
        1. Cancel all active background tasks
        2. Close WebSocket connections
        3. Close database connections
        4. Exit gracefully
    """
    logger.warning(f"Shutdown requested by admin user: {current_user.username}")

    # Broadcast shutdown notification to all connected clients
    try:
        from app.services.websocket import get_connection_manager

        ws_manager = get_connection_manager()
        await ws_manager.broadcast(
            {
                "event": "systemShutdown",
                "data": {
                    "message": "Backend server is shutting down",
                    "initiated_by": current_user.username,
                },
            }
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast shutdown notification: {e}")

    # Schedule shutdown after a brief delay to allow response to be sent
    async def delayed_shutdown():
        await asyncio.sleep(0.5)  # Wait 500ms for response to be sent
        logger.info("Initiating graceful shutdown via signal...")
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.create_task(delayed_shutdown())

    return {
        "status": "shutdown_initiated",
        "message": "Server will shutdown in 0.5 seconds",
    }


@router.post("/force-shutdown", summary="Force immediate shutdown")
async def force_shutdown(
    current_user: Annotated[User, Depends(get_current_admin)],
) -> dict[str, str]:
    """Force immediate shutdown of the backend application.

    This endpoint performs an aggressive shutdown:
    - Immediately cancels ALL asyncio tasks
    - Closes WebSocket connections without waiting
    - Sends SIGKILL for immediate termination
    - No graceful cleanup, resources may not be properly released

    ⚠️  USE WITH CAUTION - This is a forceful shutdown that may:
    - Leave database connections open
    - Lose in-progress data
    - Not flush all logs

    Use this only when normal shutdown fails or hangs.

    ⚠️  ADMIN ONLY - Requires administrator authentication.
    """
    logger.error(f"FORCE SHUTDOWN requested by admin user: {current_user.username}")

    # Broadcast urgent shutdown notification
    try:
        from app.services.websocket import get_connection_manager

        ws_manager = get_connection_manager()
        await ws_manager.broadcast(
            {
                "event": "systemForceShutdown",
                "data": {
                    "message": "Backend server is being forcefully terminated",
                    "initiated_by": current_user.username,
                    "urgent": True,
                },
            }
        )
    except Exception:
        pass  # Ignore errors in broadcast

    # Schedule aggressive shutdown
    async def immediate_force_shutdown():
        try:
            # Cancel ALL tasks immediately
            for task in asyncio.all_tasks():
                if task is not asyncio.current_task():
                    task.cancel()

            # Wait 100ms for response to be sent
            await asyncio.sleep(0.1)
        except Exception:
            pass
        finally:
            # Send SIGKILL for immediate termination
            logger.critical("Sending SIGKILL for immediate termination")
            os.kill(os.getpid(), signal.SIGKILL)

    asyncio.create_task(immediate_force_shutdown())

    return {
        "status": "force_shutdown_initiated",
        "message": "Server will be forcefully terminated in 0.1 seconds",
    }
