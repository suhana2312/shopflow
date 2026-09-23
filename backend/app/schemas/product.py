from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.category import CategoryResponse
from app.schemas.inventory import InventoryResponse

class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0, description="Product price must not be negative")
    discount_price: Optional[Decimal] = Field(None, ge=0)
    category_id: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    initial_stock: int = Field(0, ge=0)
    low_stock_threshold: int = Field(10, ge=0)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    discount_price: Optional[Decimal] = Field(None, ge=0)
    category_id: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    description: Optional[str] = None
    price: Decimal
    discount_price: Optional[Decimal] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    category: Optional[CategoryResponse] = None
    inventory: Optional[InventoryResponse] = None

    class Config:
        from_attributes = True

class ProductFilterParams(BaseModel):
    search: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    in_stock_only: Optional[bool] = None
    sort: Optional[str] = Field("created_at_desc", description="price_asc, price_desc, name_asc, created_at_desc")
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
