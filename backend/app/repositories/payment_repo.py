from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.payment import Payment, PaymentStatus

class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        return self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        ).scalar_one_or_none()

    def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        return self.db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        ).scalar_one_or_none()

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def update_status(self, payment_id: str, status: PaymentStatus, failure_reason: Optional[str] = None) -> Optional[Payment]:
        payment = self.db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
        if payment:
            payment.status = status
            if failure_reason:
                payment.failure_reason = failure_reason
            payment.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(payment)
        return payment

    def count_failed_payments(self) -> int:
        return self.db.execute(
            select(func.count(Payment.id)).where(Payment.status.in_([PaymentStatus.FAILED, PaymentStatus.TIMEOUT]))
        ).scalar() or 0
