from app.models.orders import OrderStatus

class InvalidOrderTransitionError(Exception):
    def __init__(self, current_status: OrderStatus, requested_status: OrderStatus):
        self.current_status = current_status
        self.requested_status = requested_status
        super().__init__(
            f"Invalid order status transition from {current_status.value} to {requested_status.value}"
        )

class OrderStatusService:
    """
    Centralized state machine validator for order status lifecycles.
    Prevents illegal transitions (e.g. DELIVERED -> PENDING).
    """

    ALLOWED_TRANSITIONS = {
        OrderStatus.PENDING: {
            OrderStatus.PAYMENT_PENDING,
            OrderStatus.CANCELLED
        },
        OrderStatus.PAYMENT_PENDING: {
            OrderStatus.CONFIRMED,
            OrderStatus.PAYMENT_FAILED,
            OrderStatus.CANCELLED
        },
        OrderStatus.CONFIRMED: {
            OrderStatus.PROCESSING,
            OrderStatus.CANCELLED,
            OrderStatus.REFUNDED
        },
        OrderStatus.PROCESSING: {
            OrderStatus.PACKED,
            OrderStatus.CANCELLED,
            OrderStatus.REFUNDED
        },
        OrderStatus.PACKED: {
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED,
            OrderStatus.REFUNDED
        },
        OrderStatus.SHIPPED: {
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.REFUNDED
        },
        OrderStatus.OUT_FOR_DELIVERY: {
            OrderStatus.DELIVERED,
            OrderStatus.REFUNDED
        },
        OrderStatus.DELIVERED: {
            OrderStatus.REFUNDED
        },
        OrderStatus.CANCELLED: set(),
        OrderStatus.PAYMENT_FAILED: {
            OrderStatus.PAYMENT_PENDING  # Retry payment
        },
        OrderStatus.REFUNDED: set()
    }

    @classmethod
    def can_transition(cls, current_status: OrderStatus, new_status: OrderStatus) -> bool:
        if current_status == new_status:
            return True
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, set())
        return new_status in allowed

    @classmethod
    def validate_transition(cls, current_status: OrderStatus, new_status: OrderStatus) -> None:
        if not cls.can_transition(current_status, new_status):
            raise InvalidOrderTransitionError(current_status, new_status)
