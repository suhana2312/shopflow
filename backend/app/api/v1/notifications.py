import json
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=ApiResponse[List[NotificationResponse]])
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List in-app notifications for the authenticated user."""
    service = NotificationService(db)
    items = service.list_user_notifications(current_user.id)
    responses = []
    for item in items:
        meta = json.loads(item.metadata_json) if item.metadata_json else None
        responses.append(
            NotificationResponse(
                id=item.id,
                user_id=item.user_id,
                title=item.title,
                message=item.message,
                type=item.type,
                is_read=item.is_read,
                metadata=meta,
                created_at=item.created_at
            )
        )
    return ApiResponse(data=responses)

@router.patch("/{notification_id}/read", response_model=ApiResponse[NotificationResponse])
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    service = NotificationService(db)
    item = service.mark_as_read(notification_id, current_user.id)
    meta = json.loads(item.metadata_json) if item.metadata_json else None
    resp = NotificationResponse(
        id=item.id,
        user_id=item.user_id,
        title=item.title,
        message=item.message,
        type=item.type,
        is_read=item.is_read,
        metadata=meta,
        created_at=item.created_at
    )
    return ApiResponse(data=resp, message="Notification marked as read.")
