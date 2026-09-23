from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.core.database import Base

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key = Column(String(100), primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_code = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
