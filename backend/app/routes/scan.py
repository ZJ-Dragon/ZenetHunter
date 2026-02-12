import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.exceptions import ErrorCode
from app.core.security import get_current_admin
from app.models.auth import User
from app.models.scan import ScanRequest, ScanResult
from app.services.scanner import ScannerService, get_scanner_service
from app.services.websocket import ConnectionManager, get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scan"])


@router.post("/scan/start", response_model=ScanResult, status_code=202)
async def start_scan(
    request: ScanRequest,
    current_user: Annotated[User, Depends(get_current_admin)],
    service: ScannerService = Depends(get_scanner_service),
):
    """
    Start a network scan (async).

    Returns immediately with scan_id. Actual scanning happens in background.
    Monitor progress via WebSocket events or check scan status.

    Requires admin authentication.
    """
    try:
        logger.info(
            f"Scan request received from {current_user.username}: type={request.type}"
        )
        result = await service.start_scan(request)
        logger.info(f"Scan {result.id} initiated successfully")
        return result
    except Exception as e:
        logger.error(f"Failed to start scan: {e}", exc_info=True)
        raise


@router.get(
    "/scan/status", response_model=ScanResult, summary="Get current scan status"
)
async def get_scan_status(
    current_user: Annotated[User, Depends(get_current_admin)],
    service: ScannerService = Depends(get_scanner_service),
) -> ScanResult:
    """Get the status of the current or most recent scan.

    Returns scan information including:
    - Scan ID and type
    - Current status (idle/running/completed/failed)
    - Devices found count
    - Start and end timestamps

    Requires admin authentication.
    """
    status = service.get_current_scan_status()
    return status


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, manager: ConnectionManager = Depends(get_connection_manager)
):
    """WebSocket endpoint for real-time events."""
    # Note: WebSocket auth is usually handled via query param or initial message.
    # For now, we allow connection but maybe restrict actions if we add them.
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages if needed
            # For now, we just listen/echo or ignore
            try:
                # Add timeout to prevent blocking indefinitely
                await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            except TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"event": "ping", "data": {}})
                except Exception:
                    # Connection is dead, break loop
                    break
            except WebSocketDisconnect:
                break
            except Exception:
                # Send standardized error envelope and continue loop
                try:
                    await manager.send_error(
                        websocket,
                        ErrorCode.WS_BAD_MESSAGE,
                        detail="Invalid WebSocket message format",
                    )
                except Exception:
                    # Can't send error, connection is dead
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
