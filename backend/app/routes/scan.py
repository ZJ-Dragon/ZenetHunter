from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.security import get_current_admin
from app.models.auth import User
from app.models.scan import ScanRequest, ScanResult
from app.services.scanner import ScannerService, get_scanner_service
from app.services.websocket import ConnectionManager, get_connection_manager

router = APIRouter(tags=["scan"])


@router.post("/scan/start", response_model=ScanResult, status_code=202)
async def start_scan(
    request: ScanRequest,
    admin: Annotated[User, Depends(get_current_admin)],
    service: ScannerService = Depends(get_scanner_service),
):
    """Start a network scan (async) - Admin only."""
    return await service.start_scan(request)


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
            await websocket.receive_json()
            # Optional: handle client commands via WS
    except WebSocketDisconnect:
        manager.disconnect(websocket)
