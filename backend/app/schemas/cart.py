from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.product import ProductResponse

class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(1, ge=1, description="Quantity must be at least 1")

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")

class CartItemResponse(BaseModel):
    id: str
    cart_id: str
    product_id: str
    quantity: int
    product: Optional[ProductResponse] = None
    subtotal: Decimal

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: str
    user_id: str
    items: List[CartItemResponse] = []
    total_items: int = 0
    subtotal: Decimal = Decimal("0.00")

    class Config:
        from_attributes = True
