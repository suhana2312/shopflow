from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.models.inventory import Inventory, InventoryReservation, ReservationStatus
from app.core.config import settings

class OutOfStockException(Exception):
    def __init__(self, product_id: str, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(f"Product {product_id} has insufficient stock (Requested: {requested}, Available: {available})")

class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_product_id(self, product_id: str) -> Optional[Inventory]:
        return self.db.execute(
            select(Inventory).where(Inventory.product_id == product_id)
        ).scalar_one_or_none()

    def get_with_lock(self, product_id: str) -> Optional[Inventory]:
        """
        Pessimistic row-level lock using SELECT ... FOR UPDATE.
        Blocks concurrent transactions from reading or mutating the row
        until the current transaction completes (commit/rollback).
        """
        stmt = (
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def reserve_stock(
        self,
        order_id: str,
        product_id: str,
        quantity: int,
        expiration_minutes: int = settings.RESERVATION_EXPIRATION_MINUTES
    ) -> InventoryReservation:
        """
        Atomically reserve stock under row lock:
        available_quantity -= quantity
        reserved_quantity += quantity
        Creates an InventoryReservation entry with expiration timestamp.
        """
        # Row-level lock (SELECT ... FOR UPDATE)
        inv = self.get_with_lock(product_id)
        if not inv:
            raise ValueError(f"Inventory record for product {product_id} not found")

        if inv.available_quantity < quantity:
            raise OutOfStockException(
                product_id=product_id,
                requested=quantity,
                available=inv.available_quantity
            )

        # Atomic conditional update enforcing available_quantity >= quantity at DB level
        from sqlalchemy import update
        update_stmt = (
            update(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.available_quantity >= quantity
            )
            .values(
                available_quantity=Inventory.available_quantity - quantity,
                reserved_quantity=Inventory.reserved_quantity + quantity,
                version=Inventory.version + 1,
                updated_at=datetime.utcnow()
            )
        )
        update_result = self.db.execute(update_stmt)
        if update_result.rowcount == 0:
            raise OutOfStockException(
                product_id=product_id,
                requested=quantity,
                available=0
            )

        expires_at = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        reservation = InventoryReservation(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            status=ReservationStatus.PENDING,
            expires_at=expires_at
        )
        self.db.add(reservation)
        return reservation

    def confirm_reservation(self, order_id: str) -> List[InventoryReservation]:
        """
        Transition RESERVED -> SOLD upon successful payment:
        reserved_quantity -= quantity
        sold_quantity += quantity
        reservation.status = CONFIRMED
        """
        reservations = self.db.execute(
            select(InventoryReservation).where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == ReservationStatus.PENDING
            )
        ).scalars().all()

        for res in reservations:
            inv = self.get_with_lock(res.product_id)
            if inv:
                inv.reserved_quantity -= res.quantity
                inv.sold_quantity += res.quantity
                inv.version += 1
                inv.updated_at = datetime.utcnow()
            res.status = ReservationStatus.CONFIRMED

        return list(reservations)

    def release_reservation(self, order_id: str, reason: str = "FAILED") -> List[InventoryReservation]:
        """
        Transition RESERVED -> AVAILABLE upon payment failure or order cancellation:
        available_quantity += quantity
        reserved_quantity -= quantity
        reservation.status = RELEASED
        """
        reservations = self.db.execute(
            select(InventoryReservation).where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == ReservationStatus.PENDING
            )
        ).scalars().all()

        for res in reservations:
            inv = self.get_with_lock(res.product_id)
            if inv:
                inv.available_quantity += res.quantity
                inv.reserved_quantity -= res.quantity
                inv.version += 1
                inv.updated_at = datetime.utcnow()
            res.status = ReservationStatus.RELEASED

        return list(reservations)

    def expire_stale_reservations(self) -> int:
        """
        Background task helper: scans for PENDING reservations where expires_at < now,
        restores available stock, and marks status EXPIRED.
        """
        now = datetime.utcnow()
        stale_reservations = self.db.execute(
            select(InventoryReservation).where(
                InventoryReservation.status == ReservationStatus.PENDING,
                InventoryReservation.expires_at <= now
            )
        ).scalars().all()

        expired_count = 0
        for res in stale_reservations:
            inv = self.get_with_lock(res.product_id)
            if inv:
                inv.available_quantity += res.quantity
                inv.reserved_quantity -= res.quantity
                inv.version += 1
                inv.updated_at = datetime.utcnow()
            res.status = ReservationStatus.EXPIRED
            expired_count += 1

        if expired_count > 0:
            self.db.commit()

        return expired_count

    def update_stock(self, product_id: str, available_quantity: Optional[int] = None, low_stock_threshold: Optional[int] = None) -> Optional[Inventory]:
        inv = self.get_with_lock(product_id)
        if not inv:
            return None
        if available_quantity is not None:
            inv.available_quantity = available_quantity
        if low_stock_threshold is not None:
            inv.low_stock_threshold = low_stock_threshold
        inv.updated_at = datetime.utcnow()
        inv.version += 1
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def get_low_stock_products(self) -> List[Inventory]:
        return list(
            self.db.execute(
                select(Inventory).where(Inventory.available_quantity <= Inventory.low_stock_threshold)
            ).scalars().all()
        )

    def count_out_of_stock(self) -> int:
        return self.db.execute(
            select(func.count(Inventory.id)).where(Inventory.available_quantity == 0)
        ).scalar() or 0
