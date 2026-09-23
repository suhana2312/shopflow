from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.inventory import ReservationStatus

class InventoryResponse(BaseModel):
    id: str
    product_id: str
    available_quantity: int
    reserved_quantity: int
    sold_quantity: int
    low_stock_threshold: int
    is_low_stock: bool = False
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryUpdateRequest(BaseModel):
    available_quantity: Optional[int] = Field(None, ge=0, description="Available stock quantity")
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    adjustment_reason: Optional[str] = Field(None, description="Reason for stock modification")

class InventoryReservationResponse(BaseModel):
    id: str
    order_id: str
    product_id: str
    quantity: int
    status: ReservationStatus
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
