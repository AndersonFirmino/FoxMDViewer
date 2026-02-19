"""WebSocket endpoints for real-time updates.

This module provides WebSocket connectivity for live file
updates and collaborative editing.
"""

import asyncio
import json
from pathlib import Path
from typing import Set

from starlette.endpoints import WebSocketEndpoint
from starlette.routing import Router, WebSocketRoute
from starlette.websockets import WebSocket
from rich.console import Console

console = Console()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates.

    This class provides connection management with:
    - Connection pooling
    - Broadcast messaging
    - Connection lifecycle handling

    Attributes:
        active_connections: Set of active WebSocket connections

    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(websocket)
        >>> await manager.broadcast(message)
    """

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections.add(websocket)

        console.print(
            f"[green]🔌[/green] Client connected ({len(self.active_connections)} total)"
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection from pool.

        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            self.active_connections.discard(websocket)

        console.print(
            f"[yellow]🔌[/yellow] Client disconnected "
            f"({len(self.active_connections)} total)"
        )

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connected clients.

        Args:
            message: Message dictionary to broadcast

        Example:
            >>> await manager.broadcast({
            ...     'type': 'file_update',
            ...     'path': 'example.md'
            ... })
        """
        if not self.active_connections:
            return

        message_json = json.dumps(message)

        async with self._lock:
            disconnected = set()

            for connection in self.active_connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    console.print(f"[red]✗[/red] Failed to send to client: {e}")
                    disconnected.add(connection)

            for connection in disconnected:
                self.active_connections.discard(connection)

    async def send_to(self, websocket: WebSocket, message: dict) -> None:
        """Send message to specific client.

        Args:
            websocket: Target WebSocket connection
            message: Message dictionary to send
        """
        try:
            message_json = json.dumps(message)
            await websocket.send_text(message_json)
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to send message: {e}")


connection_manager = ConnectionManager()


class MarkdownWebSocket(WebSocketEndpoint):
    """WebSocket endpoint for real-time markdown updates.

    This endpoint handles:
    - File change notifications
    - Live collaboration sync
    - Client-server communication

    Encoding: JSON text messages

    Example WebSocket URL:
        ws://localhost:8000/ws
    """

    encoding = "text"

    async def on_connect(self, websocket: WebSocket) -> None:
        """Handle new WebSocket connection.

        Args:
            websocket: WebSocket connection
        """
        await connection_manager.connect(websocket)

        await connection_manager.send_to(
            websocket,
            {"type": "connected", "message": "Successfully connected to mdviewer"},
        )

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        """Handle WebSocket disconnection.

        Args:
            websocket: WebSocket connection
            close_code: WebSocket close code
        """
        await connection_manager.disconnect(websocket)

    async def on_receive(self, websocket: WebSocket, data: str) -> None:
        """Handle received WebSocket message.

        Args:
            websocket: WebSocket connection
            data: Received text data
        """
        try:
            message = json.loads(data)
            await self._handle_message(websocket, message)
        except json.JSONDecodeError:
            await connection_manager.send_to(
                websocket, {"type": "error", "message": "Invalid JSON format"}
            )
        except Exception as e:
            await connection_manager.send_to(
                websocket, {"type": "error", "message": str(e)}
            )

    async def _handle_message(self, websocket: WebSocket, message: dict) -> None:
        """Process incoming WebSocket message.

        Args:
            websocket: WebSocket connection
            message: Parsed message dictionary
        """
        message_type = message.get("type")

        if message_type == "ping":
            await connection_manager.send_to(
                websocket, {"type": "pong", "timestamp": message.get("timestamp")}
            )

        elif message_type == "subscribe":
            await connection_manager.send_to(
                websocket,
                {"type": "subscribed", "channel": message.get("channel", "all")},
            )

        else:
            await connection_manager.send_to(
                websocket,
                {"type": "error", "message": f"Unknown message type: {message_type}"},
            )


async def broadcast_file_update(event_type: str, file_path: Path) -> None:
    """Broadcast file update to all connected clients.

    Args:
        event_type: Type of event (created, modified, deleted)
        file_path: Path to affected file

    Example:
        >>> await broadcast_file_update('modified', Path('README.md'))
    """
    await connection_manager.broadcast(
        {
            "type": "file_update",
            "event": event_type,
            "path": str(file_path),
            "filename": file_path.name,
        }
    )


def create_websocket_router() -> Router:
    """Create and configure WebSocket router.

    Returns:
        Router: Configured Starlette WebSocket router

    Example:
        >>> router = create_websocket_router()
        >>> app.mount('/ws', router)
    """
    routes = [WebSocketRoute("/", MarkdownWebSocket)]
    return Router(routes=routes)


websocket_router = create_websocket_router()
