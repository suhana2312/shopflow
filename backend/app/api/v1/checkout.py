import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limiter import checkout_rate_limiter
from app.api.deps import get_current_user
from app.models.user import User
from app.services.order_service import OrderService
from app.schemas.order import OrderCreateRequest, OrderResponse, OrderItemResponse, OrderPaymentSummary
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/checkout", tags=["Checkout"])

def format_order_response(order) -> OrderResponse:
    address_dict = json.loads(order.shipping_address) if isinstance(order.shipping_address, str) else order.shipping_address
    items = [
        OrderItemResponse(
            id=oi.id,
            product_id=oi.product_id,
            product_name=oi.product_name,
            unit_price=oi.unit_price,
            quantity=oi.quantity,
            subtotal=oi.subtotal
        )
        for oi in order.items
    ]
    payment_summary = None
    if order.payment:
        payment_summary = OrderPaymentSummary(
            id=order.payment.id,
            payment_number=order.payment.payment_number,
            transaction_id=order.payment.transaction_id,
            amount=order.payment.amount,
            status=order.payment.status.value,
            failure_reason=order.payment.failure_reason,
            created_at=order.payment.created_at
        )

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        status=order.status,
        subtotal=order.subtotal,
        discount=order.discount,
        tax=order.tax,
        shipping_fee=order.shipping_fee,
        total_amount=order.total_amount,
        shipping_address=address_dict,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=items,
        payment=payment_summary
    )

@router.post(
    "",
    response_model=ApiResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(checkout_rate_limiter)]
)
def checkout(
    req: OrderCreateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key", description="Unique client key preventing duplicate orders"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute atomic checkout:
    - Validates cart contents and active products
    - Locks inventory rows with SELECT ... FOR UPDATE
    - Atomically reserves stock (AVAILABLE -> RESERVED)
    - Calculates server-side prices, taxes, and shipping
    - Creates order and emits OrderCreated outbox event
    - Deduplicates via Idempotency-Key
    """
    service = OrderService(db)
    order = service.checkout(
        user_id=current_user.id,
        req=req,
        idempotency_key=idempotency_key
    )
    return ApiResponse(
        data=format_order_response(order),
        message="Order created and inventory reserved successfully."
    )
