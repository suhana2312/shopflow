from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DashboardMetricsResponse(BaseModel):
    total_users: int
    total_orders: int
    total_revenue: Decimal
    pending_orders: int
    failed_payments: int
    low_stock_products_count: int
    out_of_stock_products_count: int
    orders_by_status: Dict[str, int]
    revenue_by_day: List[Dict[str, Any]] = []
    top_products: List[Dict[str, Any]] = []

class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DeadLetterJobResponse(BaseModel):
    id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    status: str
    retry_count: int
    error_message: Optional[str] = None
    created_at: datetime
