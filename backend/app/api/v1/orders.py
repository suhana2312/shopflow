import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.schemas.order import OrderResponse
from app.schemas.payment import PaymentSimulationRequest, PaymentResponse
from app.schemas.common import ApiResponse, PaginatedResponse
from app.api.v1.checkout import format_order_response

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("", response_model=ApiResponse[PaginatedResponse[OrderResponse]])
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List orders for the authenticated customer."""
    service = OrderService(db)
    orders, total = service.order_repo.list_user_orders(
        user_id=current_user.id,
        skip=(page - 1) * limit,
        limit=limit
    )
    pages = math.ceil(total / limit) if limit > 0 else 1

    return ApiResponse(
        data=PaginatedResponse(
            items=[format_order_response(o) for o in orders],
            page=page,
            limit=limit,
            total=total,
            pages=pages
        )
    )

@router.get("/{order_id}", response_model=ApiResponse[OrderResponse])
def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve detailed order information with line items and payment."""
    service = OrderService(db)
    order = service.get_order(order_id, user_id=current_user.id)
    return ApiResponse(data=format_order_response(order))

@router.post("/{order_id}/cancel", response_model=ApiResponse[OrderResponse])
def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel order and automatically release reserved inventory back to available stock."""
    service = OrderService(db)
    order = service.cancel_order(order_id, user_id=current_user.id)
    return ApiResponse(
        data=format_order_response(order),
        message="Order cancelled and inventory released."
    )

@router.post("/{order_id}/simulate-payment", response_model=ApiResponse[PaymentResponse])
def simulate_payment(
    order_id: str,
    req: PaymentSimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulate payment gateway interaction:
    - Supports forced outcomes (SUCCESS, FAILED, TIMEOUT) or realistic random distribution
    - Idempotent: returns existing payment if already completed
    - SUCCESS: transitions RESERVED -> SOLD, order -> CONFIRMED
    - FAILED: transitions RESERVED -> AVAILABLE, order -> PAYMENT_FAILED
    """
    service = PaymentService(db)
    payment = service.process_payment(order_id, current_user.id, req)
    return ApiResponse(
        data=PaymentResponse.model_validate(payment),
        message=f"Payment processed with status: {payment.status.value}"
    )
