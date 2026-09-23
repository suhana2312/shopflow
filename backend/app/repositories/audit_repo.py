import json
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.audit_log import AuditLog

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        action: str,
        resource: str,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        entry = AuditLog(
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            resource=resource,
            resource_id=resource_id,
            metadata_json=json.dumps(metadata or {}, default=str)
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_logs(self, skip: int = 0, limit: int = 50) -> Tuple[List[AuditLog], int]:
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        total = self.db.execute(select(func.count(AuditLog.id))).scalar() or 0
        items = list(self.db.execute(query.offset(skip).limit(limit)).scalars().all())
        return items, total
