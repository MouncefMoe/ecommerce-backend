"""Payment API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AdminUser, CurrentUser
from src.database import get_db
from src.payments.schemas import (
    InvoiceResponse,
    PaymentMethodInfo,
    PaymentProcessRequest,
    PaymentResponse,
    RefundRequest,
)
from src.payments.service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/methods", response_model=list[PaymentMethodInfo])
async def list_payment_methods() -> list[PaymentMethodInfo]:
    """List available payment methods."""
    service = PaymentService(None)  # No DB needed for this
    methods = service.get_available_payment_methods()
    return [PaymentMethodInfo(**m) for m in methods]


@router.post("/process", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def process_payment(
    payment_data: PaymentProcessRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentResponse:
    """Process a payment for an order."""
    service = PaymentService(db)
    payment = await service.process_payment(payment_data, current_user.id)
    return PaymentResponse.model_validate(payment)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentResponse:
    """Get payment details."""
    service = PaymentService(db)
    payment = await service.get_payment_by_id(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    # Verify user owns the associated order
    from src.orders.service import OrderService
    from src.auth.models import UserRole

    order_service = OrderService(db)
    order = await order_service.get_order_by_id(payment.order_id)

    if order and order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment",
        )

    return PaymentResponse.model_validate(payment)


@router.get("/order/{order_id}", response_model=PaymentResponse)
async def get_payment_by_order(
    order_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentResponse:
    """Get payment for a specific order."""
    service = PaymentService(db)
    payment = await service.get_payment_by_order_id(order_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found for this order",
        )

    # Verify user owns the order
    from src.orders.service import OrderService
    from src.auth.models import UserRole

    order_service = OrderService(db)
    order = await order_service.get_order_by_id(order_id)

    if order and order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment",
        )

    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
async def process_refund(
    payment_id: UUID,
    refund_data: RefundRequest,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentResponse:
    """Process a refund (admin only)."""
    service = PaymentService(db)
    payment = await service.process_refund(payment_id, refund_data)
    return PaymentResponse.model_validate(payment)


@router.get("/order/{order_id}/invoice", response_model=InvoiceResponse)
async def get_invoice(
    order_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Get invoice for an order."""
    service = PaymentService(db)
    invoice_data = await service.generate_invoice(order_id, current_user.id)
    return InvoiceResponse(**invoice_data)
