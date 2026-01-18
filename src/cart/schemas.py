"""Pydantic schemas for cart."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItemBase(BaseModel):
    """Base schema for cart item."""

    product_id: UUID
    quantity: int = Field(1, ge=1)


class CartItemCreate(CartItemBase):
    """Schema for adding item to cart."""

    pass


class CartItemUpdate(BaseModel):
    """Schema for updating cart item."""

    quantity: int = Field(..., ge=1)


class ProductInCart(BaseModel):
    """Schema for product info in cart response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    price: Decimal
    stock: int
    image_url: str | None
    is_active: bool


class CartItemResponse(BaseModel):
    """Schema for cart item response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    created_at: datetime

    # Nested product info
    product: ProductInCart


class CartResponse(BaseModel):
    """Schema for cart response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    items: list[CartItemResponse]
    total: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime


class CartSummary(BaseModel):
    """Schema for cart summary (lightweight)."""

    item_count: int
    total: Decimal
