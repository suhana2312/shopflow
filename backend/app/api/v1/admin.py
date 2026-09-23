import json
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.models.orders import OrderStatus
from app.models.notification import NotificationType
from app.repositories.user_repo import UserRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.outbox_repo import OutboxRepository
from app.services.order_service import OrderService
from app.services.notification_service import NotificationService
from app.events.publisher import event_publisher
from app.schemas.admin import (
    DashboardMetricsResponse,
    AuditLogResponse,
    DeadLetterJobResponse,
)
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.schemas.user import UserResponse
from app.schemas.common import ApiResponse, PaginatedResponse
from app.api.v1.checkout import format_order_response

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/metrics", response_model=ApiResponse[DashboardMetricsResponse])
def get_dashboard_metrics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Aggregate high-level business intelligence metrics for the admin dashboard."""
    user_repo = UserRepository(db)
    order_repo = OrderRepository(db)
    inv_repo = InventoryRepository(db)
    pay_repo = PaymentRepository(db)

    total_users = user_repo.count_total()
    order_metrics = order_repo.get_metrics()
    low_stock = inv_repo.get_low_stock_products()
    out_of_stock = inv_repo.count_out_of_stock()
    failed_payments = pay_repo.count_failed_payments()

    resp = DashboardMetricsResponse(
        total_users=total_users,
        total_orders=order_metrics["total_orders"],
        total_revenue=order_metrics["total_revenue"],
        pending_orders=order_metrics["pending_orders"],
        failed_payments=failed_payments,
        low_stock_products_count=len(low_stock),
        out_of_stock_products_count=out_of_stock,
        orders_by_status=order_metrics["orders_by_status"],
        revenue_by_day=[],
        top_products=[]
    )
    return ApiResponse(data=resp)

@router.get("/orders", response_model=ApiResponse[PaginatedResponse[OrderResponse]])
def list_admin_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin view of all customer orders with filtering and pagination."""
    order_repo = OrderRepository(db)
    orders, total = order_repo.list_all_orders(
        status=status_filter,
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

@router.patch("/orders/{order_id}/status", response_model=ApiResponse[OrderResponse])
async def update_order_status(
    order_id: str,
    req: OrderStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin updates order status through state machine:
    - Enforces valid state machine transition (e.g. PACKED -> SHIPPED)
    - Records audit log
    - Dispatches in-app notification to customer
    - Broadcasts live WebSocket update to connected customer tracking screen
    """
    service = OrderService(db)
    audit_repo = AuditRepository(db)
    notif_service = NotificationService(db)

    order = service.update_order_status(order_id, req.status)

    # Audit log
    audit_repo.record(
        action="UPDATE_ORDER_STATUS",
        resource="order",
        resource_id=order.id,
        actor_id=admin.id,
        actor_email=admin.email,
        metadata={"new_status": req.status.value, "comment": req.comment}
    )

    # Customer notification
    notif_type = NotificationType.ORDER_SHIPPED if req.status == OrderStatus.SHIPPED else NotificationType.ORDER_DELIVERED
    notif_service.create(
        user_id=order.user_id,
        title=f"Order {req.status.value}",
        message=f"Your order {order.order_number} has been updated to {req.status.value}.",
        type=notif_type,
        metadata={"order_id": order.id, "status": req.status.value}
    )

    # Broadcast update via WebSockets
    await event_publisher.publish_order_status_change(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status.value,
        total_amount=str(order.total_amount)
    )

    return ApiResponse(
        data=format_order_response(order),
        message=f"Order status updated to {req.status.value}"
    )

@router.get("/users", response_model=ApiResponse[List[UserResponse]])
def list_users(
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: view all registered platform users."""
    user_repo = UserRepository(db)
    users = user_repo.list_all(skip=skip, limit=limit)
    return ApiResponse(data=[UserResponse.model_validate(u) for u in users])

@router.get("/audit-logs", response_model=ApiResponse[List[AuditLogResponse]])
def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: review operational audit logs for compliance and tracing."""
    audit_repo = AuditRepository(db)
    logs, _ = audit_repo.list_logs(skip=skip, limit=limit)
    responses = []
    for l in logs:
        meta = json.loads(l.metadata_json) if l.metadata_json else None
        responses.append(
            AuditLogResponse(
                id=l.id,
                actor_id=l.actor_id,
                actor_email=l.actor_email,
                action=l.action,
                resource=l.resource,
                resource_id=l.resource_id,
                metadata=meta,
                created_at=l.created_at
            )
        )
    return ApiResponse(data=responses)

@router.get("/dead-letter-jobs", response_model=ApiResponse[List[DeadLetterJobResponse]])
def inspect_dead_letter_queue(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: inspect failed background jobs that exhausted all retry attempts."""
    outbox_repo = OutboxRepository(db)
    dead_events = outbox_repo.list_dead_letter_jobs()
    return ApiResponse(
        data=[
            DeadLetterJobResponse(
                id=e.id,
                event_type=e.event_type,
                aggregate_type=e.aggregate_type,
                aggregate_id=e.aggregate_id,
                status=e.status.value,
                retry_count=e.retry_count,
                error_message=e.error_message,
                created_at=e.created_at
            )
            for e in dead_events
        ]
    )
