"""Cart API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.cart.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
    CartSummary,
)
from src.cart.service import CartService
from src.database import get_db

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CartResponse:
    """Get current user's cart."""
    service = CartService(db)
    cart = await service.get_or_create_cart(current_user.id)
    return CartResponse.model_validate(cart)


@router.get("/summary", response_model=CartSummary)
async def get_cart_summary(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CartSummary:
    """Get cart summary (item count and total)."""
    service = CartService(db)
    cart = await service.get_or_create_cart(current_user.id)
    return CartSummary(
        item_count=cart.item_count,
        total=cart.total,
    )


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    item_data: CartItemCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CartResponse:
    """Add item to cart."""
    service = CartService(db)
    cart = await service.add_item(current_user.id, item_data)
    return CartResponse.model_validate(cart)


@router.patch("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: UUID,
    item_data: CartItemUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CartResponse:
    """Update cart item quantity."""
    service = CartService(db)
    cart = await service.update_item(current_user.id, item_id, item_data)
    return CartResponse.model_validate(cart)


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_cart_item(
    item_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CartResponse:
    """Remove item from cart."""
    service = CartService(db)
    cart = await service.remove_item(current_user.id, item_id)
    return CartResponse.model_validate(cart)


@router.delete("", response_model=CartResponse)
async def clear_cart(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CartResponse:
    """Clear all items from cart."""
    service = CartService(db)
    cart = await service.clear_cart(current_user.id)
    return CartResponse.model_validate(cart)
