from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


PaymentApp = Literal["Google Pay", "PhonePe", "Paytm", "Card", "Cash"]
PaymentStatus = Literal["success", "pending", "failed"]
FuelType = Literal["Petrol", "Diesel", "CNG"]


class PaymentInput(BaseModel):
    transaction_time: datetime
    pump_id: str = Field(min_length=1, max_length=50)
    fuel_type: FuelType
    quantity_litres: Decimal = Field(gt=0, le=1000, max_digits=10, decimal_places=2)
    unit_price: Decimal = Field(gt=0, le=100000, max_digits=10, decimal_places=2)
    payment_app: PaymentApp
    payment_status: PaymentStatus
    gross_amount: Decimal = Field(gt=0, le=10000000, max_digits=12, decimal_places=2)
    received_amount: Decimal = Field(ge=0, le=10000000, max_digits=12, decimal_places=2)
    shift_name: str = Field(default="General", min_length=1, max_length=50)
    external_reference: str | None = Field(default=None, max_length=100)


class PaymentPatch(BaseModel):
    payment_status: PaymentStatus | None = None
    received_amount: Decimal | None = Field(default=None, ge=0, le=10000000, max_digits=12, decimal_places=2)
    payment_app: PaymentApp | None = None
    external_reference: str | None = Field(default=None, max_length=100)
