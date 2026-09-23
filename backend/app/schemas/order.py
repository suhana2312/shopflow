from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from app.models.orders import OrderStatus

class ShippingAddressInput(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    street: str = Field(..., min_length=3, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field("United States", max_length=100)
    phone: str = Field(..., min_length=7, max_length=30)

class OrderCreateRequest(BaseModel):
    shipping_address: ShippingAddressInput
    payment_method: Optional[str] = "SIMULATED_CARD"

class OrderItemResponse(BaseModel):
    id: str
    product_id: Optional[str]
    product_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal

    class Config:
        from_attributes = True

class OrderPaymentSummary(BaseModel):
    id: str
    payment_number: str
    transaction_id: str
    amount: Decimal
    status: str
    failure_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: str
    order_number: str
    user_id: str
    status: OrderStatus
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    shipping_fee: Decimal
    total_amount: Decimal
    shipping_address: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    payment: Optional[OrderPaymentSummary] = None

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    comment: Optional[str] = None
