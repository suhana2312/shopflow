import json
from typing import Dict, Set, Any
from fastapi import WebSocket
from app.core.logging import logger

class OrderWebSocketManager:
    """
    Manages active WebSocket connections subscribed to real-time order tracking channels.
    Supports multiple concurrent tabs/devices per user and clean disconnection handling.
    """
    def __init__(self):
        # order_id -> Set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, order_id: str, websocket: WebSocket):
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = set()
        self.active_connections[order_id].add(websocket)
        logger.info(f"WebSocket client connected to order channel {order_id}. Total listeners: {len(self.active_connections[order_id])}")

    def disconnect(self, order_id: str, websocket: WebSocket):
        if order_id in self.active_connections:
            self.active_connections[order_id].discard(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]
        logger.info(f"WebSocket client disconnected from order channel {order_id}")

    async def broadcast_order_update(self, order_id: str, data: Dict[str, Any]):
        """
        Pushes state change payload to all connected clients on this order's channel.
        """
        if order_id in self.active_connections:
            message = json.dumps(data)
            dead_sockets = set()
            for ws in list(self.active_connections[order_id]):
                try:
                    await ws.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket on order {order_id}: {e}")
                    dead_sockets.add(ws)

            for dead_ws in dead_sockets:
                self.disconnect(order_id, dead_ws)

ws_manager = OrderWebSocketManager()
