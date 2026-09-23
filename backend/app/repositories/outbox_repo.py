import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.outbox import OutboxEvent, OutboxStatus

class OutboxRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_event(
        self,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any]
    ) -> OutboxEvent:
        """
        Enqueues an outbox event within the ongoing database transaction.
        Guarantees that event persistence is atomic with database state changes.
        """
        event = OutboxEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload_json=json.dumps(payload, default=str),
            status=OutboxStatus.PENDING
        )
        self.db.add(event)
        return event

    def get_pending_events(self, limit: int = 50) -> List[OutboxEvent]:
        return list(
            self.db.execute(
                select(OutboxEvent)
                .where(OutboxEvent.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]))
                .where(OutboxEvent.retry_count < 3)
                .order_by(OutboxEvent.created_at.asc())
                .limit(limit)
            ).scalars().all()
        )

    def mark_published(self, event_id: str) -> Optional[OutboxEvent]:
        event = self.db.execute(select(OutboxEvent).where(OutboxEvent.id == event_id)).scalar_one_or_none()
        if event:
            event.status = OutboxStatus.PUBLISHED
            event.processed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(event)
        return event

    def mark_failed(self, event_id: str, error_message: str, max_retries: int = 3) -> Optional[OutboxEvent]:
        event = self.db.execute(select(OutboxEvent).where(OutboxEvent.id == event_id)).scalar_one_or_none()
        if event:
            event.retry_count += 1
            event.error_message = error_message
            if event.retry_count >= max_retries:
                event.status = OutboxStatus.DEAD_LETTER
            else:
                event.status = OutboxStatus.FAILED
            event.processed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(event)
        return event

    def list_dead_letter_jobs(self, limit: int = 50) -> List[OutboxEvent]:
        return list(
            self.db.execute(
                select(OutboxEvent)
                .where(OutboxEvent.status == OutboxStatus.DEAD_LETTER)
                .order_by(OutboxEvent.created_at.desc())
                .limit(limit)
            ).scalars().all()
        )
