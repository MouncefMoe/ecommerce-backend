"""Pydantic schemas for payments."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.payments.models import PaymentMethod, PaymentStatus


class PaymentProcessRequest(BaseModel):
    """Schema for processing a payment."""

    order_id: UUID
    method: PaymentMethod
    # Mock card details (in production, use tokenized payment info)
    card_number: str | None = Field(None, min_length=13, max_length=19)
    card_expiry: str | None = Field(None, pattern=r"^\d{2}/\d{2}$")
    card_cvv: str | None = Field(None, min_length=3, max_length=4)
    card_holder_name: str | None = None


class RefundRequest(BaseModel):
    """Schema for requesting a refund."""

    amount: Decimal | None = Field(None, ge=0, description="Amount to refund. If not provided, full refund.")
    reason: str | None = None


class PaymentResponse(BaseModel):
    """Schema for payment response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    amount: Decimal
    status: PaymentStatus
    method: PaymentMethod
    transaction_id: str | None
    failure_reason: str | None
    refunded_amount: Decimal
    is_successful: bool
    can_refund: bool
    paid_at: datetime | None
    refunded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PaymentMethodInfo(BaseModel):
    """Schema for payment method information."""

    method: PaymentMethod
    name: str
    description: str
    is_available: bool = True


class InvoiceItem(BaseModel):
    """Schema for invoice line item."""

    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""

    invoice_number: str
    order_number: str
    customer_name: str
    customer_email: str
    billing_address: dict | None
    items: list[InvoiceItem]
    subtotal: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    payment_method: str
    payment_status: str
    paid_at: datetime | None
    created_at: datetime
