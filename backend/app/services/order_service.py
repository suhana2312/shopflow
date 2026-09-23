import json
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.orders import Order, OrderItem, OrderStatus
from app.models.idempotency import IdempotencyKey
from app.repositories.order_repo import OrderRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.inventory_repo import InventoryRepository, OutOfStockException
from app.repositories.product_repo import ProductRepository
from app.repositories.outbox_repo import OutboxRepository
from app.services.order_status_service import OrderStatusService, InvalidOrderTransitionError
from app.schemas.order import OrderCreateRequest, OrderResponse, OrderStatusUpdate
from app.core.config import settings
from app.core.logging import logger

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.product_repo = ProductRepository(db)
        self.outbox_repo = OutboxRepository(db)

    def check_idempotency(self, key: str, user_id: str) -> Optional[dict]:
        record = self.db.query(IdempotencyKey).filter(
            IdempotencyKey.key == key,
            IdempotencyKey.user_id == user_id
        ).first()
        if record:
            return json.loads(record.response_body)
        return None

    def save_idempotency(self, key: str, user_id: str, endpoint: str, response_dict: dict, status_code: int = 201):
        ik = IdempotencyKey(
            key=key,
            user_id=user_id,
            endpoint=endpoint,
            request_hash="",
            response_code=status_code,
            response_body=json.dumps(response_dict, default=str),
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        self.db.add(ik)
        self.db.commit()

    def checkout(
        self,
        user_id: str,
        req: OrderCreateRequest,
        idempotency_key: Optional[str] = None
    ) -> Order:
        """
        Atomic checkout flow:
        1. Check idempotency key if provided
        2. Validate cart and active products
        3. Lock inventory rows & reserve stock (SELECT ... FOR UPDATE)
        4. Calculate subtotal, tax, and shipping server-side
        5. Persist Order and OrderItems
        6. Enqueue OrderCreated in Transactional Outbox
        7. Clear user cart
        8. Commit transaction
        """
        # Idempotency check
        if idempotency_key:
            cached_order = self.check_idempotency(idempotency_key, user_id)
            if cached_order:
                logger.info(f"Returning cached order for idempotency key: {idempotency_key}")
                existing_order = self.order_repo.get_by_id(cached_order["id"])
                if existing_order:
                    return existing_order

        cart = self.cart_repo.get_with_items(user_id)
        if not cart.items or len(cart.items) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CART_EMPTY", "message": "Cannot checkout with an empty cart."}
            )

        # Server-side price calculation
        subtotal = Decimal("0.00")
        order_items_to_create = []

        # Validate products and prices
        for item in cart.items:
            product = self.product_repo.get_by_id(item.product_id)
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "PRODUCT_UNAVAILABLE",
                        "message": f"Product '{item.product_id}' is no longer active or available."
                    }
                )
            
            unit_price = Decimal(str(product.discount_price if product.discount_price is not None else product.price))
            item_subtotal = unit_price * item.quantity
            subtotal += item_subtotal

            order_items_to_create.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=unit_price,
                    quantity=item.quantity,
                    subtotal=item_subtotal
                )
            )

        tax = (subtotal * Decimal(str(settings.TAX_RATE))).quantize(Decimal("0.01"))
        shipping_fee = Decimal(str(settings.FLAT_SHIPPING_FEE))
        total_amount = subtotal + tax + shipping_fee

        order_number = self.order_repo.generate_order_number()

        # Atomic transaction boundary
        try:
            order = Order(
                order_number=order_number,
                user_id=user_id,
                status=OrderStatus.PENDING,
                subtotal=subtotal,
                discount=Decimal("0.00"),
                tax=tax,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                shipping_address=json.dumps(req.shipping_address.model_dump())
            )
            self.db.add(order)
            self.db.flush()

            # Reserve inventory with pessimistic row lock
            for item in cart.items:
                self.inventory_repo.reserve_stock(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity
                )

            # Attach order items
            for oi in order_items_to_create:
                oi.order_id = order.id
                self.db.add(oi)

            # Record OrderCreated event in Transactional Outbox
            self.outbox_repo.record_event(
                event_type="OrderCreated",
                aggregate_type="Order",
                aggregate_id=order.id,
                payload={
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "user_id": user_id,
                    "total_amount": str(order.total_amount),
                    "items": [
                        {"product_id": oi.product_id, "quantity": oi.quantity, "subtotal": str(oi.subtotal)}
                        for oi in order_items_to_create
                    ],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )

            # Transition to PAYMENT_PENDING
            order.status = OrderStatus.PAYMENT_PENDING

            # Clear cart items
            self.cart_repo.clear_cart(cart.id)

            self.db.commit()
            self.db.refresh(order)

            # Save idempotency record
            if idempotency_key:
                resp_data = {"id": order.id, "order_number": order.order_number, "status": order.status.value}
                self.save_idempotency(idempotency_key, user_id, "/api/v1/checkout", resp_data)

            return order

        except OutOfStockException as oos:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "OUT_OF_STOCK",
                    "message": str(oos),
                    "details": {"product_id": oos.product_id, "requested": oos.requested, "available": oos.available}
                }
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Checkout transaction failed: {str(e)}")
            raise

    def get_order(self, order_id: str, user_id: Optional[str] = None, is_admin: bool = False) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ORDER_NOT_FOUND", "message": f"Order {order_id} not found"}
            )
        if not is_admin and user_id and order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "UNAUTHORIZED_ORDER_ACCESS", "message": "You are not authorized to view this order."}
            )
        return order

    def update_order_status(self, order_id: str, new_status: OrderStatus) -> Order:
        order = self.get_order(order_id, is_admin=True)
        try:
            OrderStatusService.validate_transition(order.status, new_status)
        except InvalidOrderTransitionError as err:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "INVALID_STATE_TRANSITION", "message": str(err)}
            )

        updated_order = self.order_repo.update_status(order_id, new_status)

        # Enqueue event to outbox
        self.outbox_repo.record_event(
            event_type=f"Order{new_status.value.replace('_', '').title()}",
            aggregate_type="Order",
            aggregate_id=order_id,
            payload={
                "order_id": order_id,
                "order_number": updated_order.order_number,
                "status": new_status.value,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        self.db.commit()
        return updated_order

    def cancel_order(self, order_id: str, user_id: str, is_admin: bool = False) -> Order:
        order = self.get_order(order_id, user_id=user_id, is_admin=is_admin)
        if order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REFUNDED):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ORDER_CANNOT_BE_CANCELLED", "message": f"Order in status {order.status.value} cannot be cancelled."}
            )

        # Release any pending inventory reservations
        self.inventory_repo.release_reservation(order.id, reason="CANCELLED")
        return self.update_order_status(order_id, OrderStatus.CANCELLED)
