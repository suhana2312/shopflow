from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.models.notification import NotificationType

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationType
    is_read: bool
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
