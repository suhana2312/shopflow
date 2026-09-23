from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from app.models.payment import PaymentStatus

class PaymentSimulationRequest(BaseModel):
    outcome: Optional[str] = Field("RANDOM", description="Force outcome: RANDOM, SUCCESS, FAILED, TIMEOUT")
    payment_method: Optional[str] = Field("SIMULATED_CARD", description="SIMULATED_CARD, SIMULATED_WALLET, SIMULATED_BANK")

class PaymentResponse(BaseModel):
    id: str
    order_id: str
    payment_number: str
    transaction_id: str
    amount: Decimal
    status: PaymentStatus
    failure_reason: Optional[str] = None
    payment_method: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
