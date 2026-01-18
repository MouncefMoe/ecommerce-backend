"""Order API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AdminUser, CurrentUser
from src.auth.models import UserRole
from src.database import get_db
from src.orders.models import OrderStatus
from src.orders.schemas import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from src.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=OrderListResponse)
async def list_my_orders(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = None,
) -> OrderListResponse:
    """List current user's orders."""
    service = OrderService(db)
    skip = (page - 1) * size

    orders, total = await service.get_user_orders(
        user_id=current_user.id,
        skip=skip,
        limit=size,
        status=status,
    )

    pages = (total + size - 1) // size

    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    """Get order by ID."""
    service = OrderService(db)
    order = await service.get_order_by_id(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check authorization (user must own order or be admin)
    is_admin = current_user.role == UserRole.ADMIN
    if order.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order",
        )

    return OrderResponse.model_validate(order)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    """Create a new order from cart."""
    service = OrderService(db)
    order = await service.create_order_from_cart(current_user.id, order_data)
    return OrderResponse.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    reason: str | None = None,
) -> OrderResponse:
    """Cancel an order."""
    service = OrderService(db)
    is_admin = current_user.role == UserRole.ADMIN

    order = await service.cancel_order(
        order_id=order_id,
        user_id=current_user.id,
        is_admin=is_admin,
        reason=reason,
    )

    return OrderResponse.model_validate(order)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status_data: OrderStatusUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    """Update order status (seller/admin only)."""
    # Only sellers and admins can update order status
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update order status",
        )

    service = OrderService(db)
    is_admin = current_user.role == UserRole.ADMIN

    order = await service.update_order_status(
        order_id=order_id,
        status_data=status_data,
        user_id=current_user.id,
        is_admin=is_admin,
    )

    return OrderResponse.model_validate(order)


# Admin endpoints
@router.get("/admin/all", response_model=OrderListResponse)
async def list_all_orders(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = None,
    user_id: UUID | None = None,
) -> OrderListResponse:
    """List all orders (admin only)."""
    service = OrderService(db)
    skip = (page - 1) * size

    orders, total = await service.get_all_orders(
        skip=skip,
        limit=size,
        status=status,
        user_id=user_id,
    )

    pages = (total + size - 1) // size

    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )
