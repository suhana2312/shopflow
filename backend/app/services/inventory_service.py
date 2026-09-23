from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.inventory import Inventory
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.inventory import InventoryResponse, InventoryUpdateRequest
from app.core.redis import redis_client

class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.inventory_repo = InventoryRepository(db)
        self.audit_repo = AuditRepository(db)

    def get_by_product_id(self, product_id: str) -> InventoryResponse:
        inv = self.inventory_repo.get_by_product_id(product_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INVENTORY_NOT_FOUND", "message": f"Inventory for product {product_id} not found."}
            )
        resp = InventoryResponse.model_validate(inv)
        resp.is_low_stock = inv.available_quantity <= inv.low_stock_threshold
        return resp

    def update_stock(
        self,
        product_id: str,
        req: InventoryUpdateRequest,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None
    ) -> InventoryResponse:
        inv = self.inventory_repo.update_stock(
            product_id=product_id,
            available_quantity=req.available_quantity,
            low_stock_threshold=req.low_stock_threshold
        )
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INVENTORY_NOT_FOUND", "message": f"Inventory for product {product_id} not found."}
            )

        # Audit logging
        self.audit_repo.record(
            action="ADJUST_INVENTORY",
            resource="inventory",
            resource_id=inv.id,
            actor_id=actor_id,
            actor_email=actor_email,
            metadata={
                "product_id": product_id,
                "new_available": inv.available_quantity,
                "threshold": inv.low_stock_threshold,
                "reason": req.adjustment_reason
            }
        )

        # Invalidate product cache
        redis_client.delete(f"product:{product_id}")
        redis_client.delete_pattern("products:*")

        resp = InventoryResponse.model_validate(inv)
        resp.is_low_stock = inv.available_quantity <= inv.low_stock_threshold
        return resp

    def list_low_stock(self) -> List[InventoryResponse]:
        low_stock_list = self.inventory_repo.get_low_stock_products()
        results = []
        for inv in low_stock_list:
            resp = InventoryResponse.model_validate(inv)
            resp.is_low_stock = True
            results.append(resp)
        return results

    def expire_stale_reservations(self) -> int:
        return self.inventory_repo.expire_stale_reservations()
