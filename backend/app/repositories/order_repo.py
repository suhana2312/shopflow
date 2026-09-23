from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, desc
from app.models.orders import Order, OrderItem, OrderStatus
from app.models.payment import Payment

class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def generate_order_number(self) -> str:
        import uuid
        year = datetime.utcnow().year
        count = self.db.execute(select(func.count(Order.id))).scalar() or 0
        suffix = uuid.uuid4().hex[:6].upper()
        return f"ORD-{year}-{(count + 1):04d}-{suffix}"

    def get_by_id(self, order_id: str) -> Optional[Order]:
        return self.db.execute(
            select(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.payment),
                joinedload(Order.reservations)
            )
            .where(Order.id == order_id)
        ).unique().scalar_one_or_none()

    def get_by_order_number(self, order_number: str) -> Optional[Order]:
        return self.db.execute(
            select(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.payment)
            )
            .where(Order.order_number == order_number)
        ).unique().scalar_one_or_none()

    def create(self, order: Order, items: List[OrderItem]) -> Order:
        self.db.add(order)
        self.db.flush()  # assign ID
        for item in items:
            item.order_id = order.id
            self.db.add(item)
        self.db.commit()
        self.db.refresh(order)
        return order

    def list_user_orders(self, user_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[Order], int]:
        query = (
            select(Order)
            .options(joinedload(Order.items), joinedload(Order.payment))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        total = self.db.execute(
            select(func.count(Order.id)).where(Order.user_id == user_id)
        ).scalar() or 0

        orders = list(self.db.execute(query.offset(skip).limit(limit)).unique().scalars().all())
        return orders, total

    def list_all_orders(self, status: Optional[OrderStatus] = None, skip: int = 0, limit: int = 50) -> Tuple[List[Order], int]:
        query = (
            select(Order)
            .options(joinedload(Order.items), joinedload(Order.payment))
            .order_by(Order.created_at.desc())
        )
        count_query = select(func.count(Order.id))

        if status:
            query = query.where(Order.status == status)
            count_query = count_query.where(Order.status == status)

        total = self.db.execute(count_query).scalar() or 0
        orders = list(self.db.execute(query.offset(skip).limit(limit)).unique().scalars().all())
        return orders, total

    def update_status(self, order_id: str, new_status: OrderStatus) -> Optional[Order]:
        order = self.get_by_id(order_id)
        if order:
            order.status = new_status
            order.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(order)
        return order

    def get_metrics(self) -> Dict[str, Any]:
        total_orders = self.db.execute(select(func.count(Order.id))).scalar() or 0
        total_revenue = self.db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0.00)).where(
                Order.status.in_([
                    OrderStatus.CONFIRMED,
                    OrderStatus.PROCESSING,
                    OrderStatus.PACKED,
                    OrderStatus.SHIPPED,
                    OrderStatus.OUT_FOR_DELIVERY,
                    OrderStatus.DELIVERED
                ])
            )
        ).scalar() or Decimal("0.00")

        pending_orders = self.db.execute(
            select(func.count(Order.id)).where(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.PAYMENT_PENDING])
            )
        ).scalar() or 0

        # Orders by status
        status_counts = self.db.execute(
            select(Order.status, func.count(Order.id)).group_by(Order.status)
        ).all()
        orders_by_status = {str(status.value): count for status, count in status_counts}

        return {
            "total_orders": total_orders,
            "total_revenue": Decimal(str(total_revenue)),
            "pending_orders": pending_orders,
            "orders_by_status": orders_by_status
        }
