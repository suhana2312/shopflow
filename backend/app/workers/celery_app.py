from celery import Celery
from kombu import Exchange, Queue
from app.core.config import settings

celery_app = Celery(
    "shopflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

# Dead Letter Exchange and Queue setup
default_exchange = Exchange("shopflow.events", type="topic")
dlx_exchange = Exchange("shopflow.dlx", type="direct")

celery_app.conf.task_queues = (
    Queue(
        "shopflow.orders",
        default_exchange,
        routing_key="order.#",
        queue_arguments={"x-dead-letter-exchange": "shopflow.dlx", "x-dead-letter-routing-key": "dead_letter"}
    ),
    Queue(
        "shopflow.payments",
        default_exchange,
        routing_key="payment.#",
        queue_arguments={"x-dead-letter-exchange": "shopflow.dlx", "x-dead-letter-routing-key": "dead_letter"}
    ),
    Queue(
        "shopflow.notifications",
        default_exchange,
        routing_key="notification.#",
        queue_arguments={"x-dead-letter-exchange": "shopflow.dlx", "x-dead-letter-routing-key": "dead_letter"}
    ),
    Queue(
        "shopflow.dlq",
        dlx_exchange,
        routing_key="dead_letter"
    ),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=5,
    task_max_retries=3,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "cleanup-expired-reservations": {
            "task": "app.workers.tasks.cleanup_expired_reservations_task",
            "schedule": 60.0,  # every 60 seconds
        },
        "sweep-outbox-events": {
            "task": "app.workers.tasks.sweep_outbox_events_task",
            "schedule": 15.0,  # every 15 seconds
        },
    }
)
