from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.services.inventory_service import InventoryService
from app.schemas.inventory import InventoryResponse, InventoryUpdateRequest
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("/low-stock", response_model=ApiResponse[List[InventoryResponse]])
def get_low_stock_products(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: view all inventory records where available stock is below low-stock threshold."""
    service = InventoryService(db)
    items = service.list_low_stock()
    return ApiResponse(data=items)

@router.get("/{product_id}", response_model=ApiResponse[InventoryResponse])
def get_product_inventory(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve inventory details (available, reserved, sold quantities) for a product."""
    service = InventoryService(db)
    inv = service.get_by_product_id(product_id)
    return ApiResponse(data=inv)

@router.patch("/{product_id}", response_model=ApiResponse[InventoryResponse])
def update_inventory_stock(
    product_id: str,
    req: InventoryUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: adjust inventory quantities and update threshold with audit logging."""
    service = InventoryService(db)
    inv = service.update_stock(
        product_id=product_id,
        req=req,
        actor_id=admin.id,
        actor_email=admin.email
    )
    return ApiResponse(data=inv, message="Inventory successfully updated.")
