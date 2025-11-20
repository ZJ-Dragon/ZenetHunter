from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.models.scan import ScanRequest, ScanResult
from app.services.scanner import ScannerService, get_scanner_service
from app.services.websocket import ConnectionManager, get_connection_manager

router = APIRouter(tags=["scan"])


@router.post("/scan/start", response_model=ScanResult, status_code=202)
async def start_scan(
    request: ScanRequest, service: ScannerService = Depends(get_scanner_service)
):
    """Start a network scan (async)."""
    return await service.start_scan(request)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, manager: ConnectionManager = Depends(get_connection_manager)
):
    """WebSocket endpoint for real-time events."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages if needed
            # For now, we just listen/echo or ignore
            await websocket.receive_json()
            # Optional: handle client commands via WS
    except WebSocketDisconnect:
        manager.disconnect(websocket)
