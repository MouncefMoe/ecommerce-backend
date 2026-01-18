"""Pydantic schemas for orders."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.orders.models import OrderStatus


class AddressSchema(BaseModel):
    """Schema for address data."""

    full_name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=20)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str | None = Field(None, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)


class OrderItemBase(BaseModel):
    """Base schema for order item."""

    product_id: UUID
    quantity: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    """Schema for creating an order from cart."""

    shipping_address: AddressSchema
    billing_address: AddressSchema | None = None
    notes: str | None = None


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""

    status: OrderStatus
    notes: str | None = None


class OrderItemResponse(BaseModel):
    """Schema for order item response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID | None
    product_name: str
    product_sku: str
    product_image_url: str | None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class PaymentSummary(BaseModel):
    """Schema for payment summary in order response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    method: str
    amount: Decimal
    paid_at: datetime | None


class OrderResponse(BaseModel):
    """Schema for order response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    user_id: UUID
    status: OrderStatus
    subtotal: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    shipping_address: dict
    billing_address: dict | None
    notes: str | None
    item_count: int
    can_cancel: bool
    is_paid: bool
    items: list[OrderItemResponse]
    payment: PaymentSummary | None = None
    created_at: datetime
    updated_at: datetime
    shipped_at: datetime | None
    delivered_at: datetime | None
    cancelled_at: datetime | None


class OrderListResponse(BaseModel):
    """Schema for paginated order list response."""

    items: list[OrderResponse]
    total: int
    page: int
    size: int
    pages: int


class OrderSummary(BaseModel):
    """Schema for lightweight order summary."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    status: OrderStatus
    total_amount: Decimal
    item_count: int
    created_at: datetime
