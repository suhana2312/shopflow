import uuid
import random
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.payment import Payment, PaymentStatus
from app.models.orders import Order, OrderStatus
from app.models.notification import Notification, NotificationType
from app.repositories.payment_repo import PaymentRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.outbox_repo import OutboxRepository
from app.schemas.payment import PaymentSimulationRequest, PaymentResponse
from app.core.config import settings
from app.core.logging import logger

class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.outbox_repo = OutboxRepository(db)

    def process_payment(
        self,
        order_id: str,
        user_id: str,
        req: PaymentSimulationRequest
    ) -> Payment:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ORDER_NOT_FOUND", "message": f"Order {order_id} not found"}
            )

        if order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "UNAUTHORIZED_PAYMENT", "message": "Cannot pay for another user's order"}
            )

        # Payment Idempotency check: if payment already exists for this order
        existing_payment = self.payment_repo.get_by_order_id(order_id)
        if existing_payment:
            logger.info(f"Payment idempotency hit: returning existing payment {existing_payment.id} for order {order_id}")
            return existing_payment

        # Determine outcome
        outcome = req.outcome.upper() if req.outcome else "RANDOM"
        if outcome == "RANDOM":
            rand_val = random.random()
            if rand_val < settings.PAYMENT_SUCCESS_RATE:
                outcome = "SUCCESS"
            elif rand_val < (settings.PAYMENT_SUCCESS_RATE + settings.PAYMENT_TIMEOUT_RATE):
                outcome = "TIMEOUT"
            else:
                outcome = "FAILED"

        payment_number = f"PAY-{datetime.utcnow().year}-{random.randint(100000, 999999)}"
        transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"

        payment = Payment(
            order_id=order.id,
            payment_number=payment_number,
            transaction_id=transaction_id,
            amount=order.total_amount,
            status=PaymentStatus.PENDING,
            payment_method=req.payment_method or "SIMULATED_CARD"
        )
        self.db.add(payment)
        self.db.flush()

        if outcome == "SUCCESS":
            payment.status = PaymentStatus.SUCCESS
            order.status = OrderStatus.CONFIRMED
            order.updated_at = datetime.utcnow()

            # Confirm inventory reservations: RESERVED -> SOLD
            self.inventory_repo.confirm_reservation(order.id)

            # In-app notification
            notif = Notification(
                user_id=order.user_id,
                title="Payment Confirmed",
                message=f"Your payment of ${order.total_amount:.2f} for order {order.order_number} was successful!",
                type=NotificationType.PAYMENT_SUCCESS
            )
            self.db.add(notif)

            # Outbox event
            self.outbox_repo.record_event(
                event_type="PaymentSucceeded",
                aggregate_type="Payment",
                aggregate_id=payment.id,
                payload={
                    "payment_id": payment.id,
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "amount": str(payment.amount),
                    "transaction_id": payment.transaction_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )

        elif outcome == "FAILED":
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "Simulated card authorization decline / insufficient funds"
            order.status = OrderStatus.PAYMENT_FAILED
            order.updated_at = datetime.utcnow()

            # Release inventory reservations: RESERVED -> AVAILABLE
            self.inventory_repo.release_reservation(order.id, reason="PAYMENT_FAILED")

            notif = Notification(
                user_id=order.user_id,
                title="Payment Failed",
                message=f"Payment for order {order.order_number} failed. Your reserved items have been restored.",
                type=NotificationType.PAYMENT_FAILED
            )
            self.db.add(notif)

            # Outbox event
            self.outbox_repo.record_event(
                event_type="PaymentFailed",
                aggregate_type="Payment",
                aggregate_id=payment.id,
                payload={
                    "payment_id": payment.id,
                    "order_id": order.id,
                    "reason": payment.failure_reason,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )

        elif outcome == "TIMEOUT":
            payment.status = PaymentStatus.TIMEOUT
            payment.failure_reason = "Gateway response timed out after 30 seconds"
            order.status = OrderStatus.PAYMENT_PENDING
            order.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payment)
        return payment
