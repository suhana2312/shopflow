import json
from typing import Dict, Any, Optional
from app.core.logging import logger
from app.websocket.connection_manager import ws_manager

class EventPublisher:
    """
    Dispatches business domain events to broker/workers and real-time WebSocket clients.
    """
    @staticmethod
    async def publish_order_status_change(order_id: str, order_number: str, status: str, total_amount: Optional[str] = None):
        payload = {
            "order_id": order_id,
            "order_number": order_number,
            "status": status,
            "total_amount": total_amount,
            "timestamp": None
        }
        from datetime import datetime
        payload["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Push to real-time WebSockets
        try:
            await ws_manager.broadcast_order_update(order_id, payload)
        except Exception as e:
            logger.warning(f"Failed to broadcast WebSocket update for order {order_id}: {e}")

    @staticmethod
    def trigger_celery_task(task_name: str, *args, **kwargs):
        """Safely dispatch to Celery if broker is available."""
        try:
            from app.workers.celery_app import celery_app
            celery_app.send_task(task_name, args=args, kwargs=kwargs)
        except Exception as e:
            logger.warning(f"Could not dispatch Celery task {task_name} (broker offline/resilient mode): {e}")

event_publisher = EventPublisher()
