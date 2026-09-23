from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationResponse

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def list_user_notifications(self, user_id: str, limit: int = 50) -> List[Notification]:
        return list(
            self.db.execute(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
            ).scalars().all()
        )

    def mark_as_read(self, notification_id: str, user_id: str) -> Notification:
        notif = self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).scalar_one_or_none()

        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notification not found"}
            )

        notif.is_read = True
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def create(
        self,
        user_id: str,
        title: str,
        message: str,
        type: NotificationType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        import json
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            metadata_json=json.dumps(metadata or {}, default=str)
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif
