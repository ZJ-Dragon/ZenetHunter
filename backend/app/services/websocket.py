import logging
import uuid

from fastapi import WebSocket

from app.core.exceptions import ErrorCode

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager for broadcasting events.
    Singleton pattern to ensure global access.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.active_connections: list[WebSocket] = []
        self._initialized = True

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket client connected. Total: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"WebSocket client disconnected. Total: {len(self.active_connections)}"
            )

    async def broadcast(self, message: dict):
        """Broadcast a JSON message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # If sending fails, assume client is gone
                logger.debug(f"Failed to send WebSocket message: {e}")
                disconnected.append(connection)

        for dead_conn in disconnected:
            self.disconnect(dead_conn)

    async def close_all(self):
        """Close all WebSocket connections gracefully."""
        logger.info(f"Closing {len(self.active_connections)} WebSocket connections...")
        connections_to_close = list(self.active_connections)
        for connection in connections_to_close:
            try:
                await connection.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
            finally:
                self.disconnect(connection)
        logger.info("All WebSocket connections closed")

    async def send_error(
        self,
        websocket: WebSocket,
        code: ErrorCode | str,
        detail: str,
        correlation_id: str | None = None,
    ):
        """Send a standardized error envelope to a single WS client."""
        cid = correlation_id or str(uuid.uuid4())
        payload = {
            "event": "error",
            "code": code.value if isinstance(code, ErrorCode) else str(code),
            "detail": detail,
            "correlation_id": cid,
        }
        try:
            await websocket.send_json(payload)
        except Exception:
            # Treat as disconnected
            self.disconnect(websocket)

    async def close_with_error(
        self, websocket: WebSocket, code: ErrorCode | str, detail: str
    ):
        """Send error then close connection."""
        await self.send_error(websocket, code, detail)
        try:
            await websocket.close()
        except Exception:
            self.disconnect(websocket)


# Global accessor
def get_connection_manager() -> ConnectionManager:
    return ConnectionManager()
