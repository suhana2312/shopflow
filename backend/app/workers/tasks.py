import json
import asyncio
from datetime import datetime
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.outbox_repo import OutboxRepository
from app.repositories.order_repo import OrderRepository
from app.websocket.connection_manager import ws_manager
from app.core.logging import logger

@celery_app.task(name="app.workers.tasks.cleanup_expired_reservations_task")
def cleanup_expired_reservations_task():
    """
    Scheduled task (Celery Beat): Scans for unconfirmed reservations older than 10 minutes,
    restores stock, and marks them EXPIRED.
    """
    db = SessionLocal()
    try:
        repo = InventoryRepository(db)
        expired_count = repo.expire_stale_reservations()
        if expired_count > 0:
            logger.info(f"[Celery Beat] Cleaned up {expired_count} expired inventory reservations.")
        return {"expired_count": expired_count}
    except Exception as e:
        logger.error(f"[Celery Beat] Failed to clean up expired reservations: {e}")
        raise
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5, name="app.workers.tasks.sweep_outbox_events_task")
def sweep_outbox_events_task(self):
    """
    Outbox Worker Task: Reads pending events from `outbox_events` table,
    dispatches notifications, triggers WebSockets, and marks events PUBLISHED.
    If failures exceed max_retries, OutboxRepository routes them to DEAD_LETTER.
    """
    db = SessionLocal()
    try:
        repo = OutboxRepository(db)
        pending_events = repo.get_pending_events(limit=25)
        processed = 0

        for event in pending_events:
            try:
                payload = json.loads(event.payload_json)
                
                # If order-related event, trigger WebSocket broadcast
                if event.aggregate_type == "Order" and "order_id" in payload:
                    order_id = payload["order_id"]
                    # Non-blocking async event loop trigger for WebSocket broadcast
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(
                                ws_manager.broadcast_order_update(order_id, payload)
                            )
                        else:
                            loop.run_until_complete(
                                ws_manager.broadcast_order_update(order_id, payload)
                            )
                    except Exception as ws_err:
                        logger.warning(f"Could not broadcast to WebSocket manager in worker: {ws_err}")

                repo.mark_published(event.id)
                processed += 1
            except Exception as item_err:
                logger.error(f"Error dispatching outbox event {event.id}: {item_err}")
                repo.mark_failed(event.id, str(item_err))

        return {"processed": processed}
    except Exception as e:
        logger.error(f"Sweep outbox events failed: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()

@celery_app.task(name="app.workers.tasks.generate_invoice_task")
def generate_invoice_task(order_id: str):
    """Simulate asynchronous invoice PDF rendering and archiving."""
    logger.info(f"Generating invoice PDF for order {order_id}...")
    return {"order_id": order_id, "invoice_url": f"https://shopflow-invoices.s3.amazonaws.com/inv-{order_id}.pdf"}

@celery_app.task(name="app.workers.tasks.send_async_email_task")
def send_async_email_task(recipient_email: str, subject: str, content: str):
    """Simulate asynchronous email dispatch (e.g. via AWS SES or SendGrid)."""
    logger.info(f"Simulating async email delivery to {recipient_email} - Subject: {subject}")
    return {"recipient": recipient_email, "delivered_at": datetime.utcnow().isoformat() + "Z"}
