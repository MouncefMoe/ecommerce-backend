"""Payment service with business logic."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import BadRequestError, NotFoundError
from src.orders.models import Order, OrderStatus
from src.orders.service import OrderService
from src.payments.gateway import payment_gateway
from src.payments.models import Payment, PaymentMethod, PaymentStatus
from src.payments.schemas import PaymentProcessRequest, RefundRequest


class PaymentService:
    """Service for payment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_payment_by_id(self, payment_id: UUID) -> Payment | None:
        """Get payment by ID."""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_order_id(self, order_id: UUID) -> Payment | None:
        """Get payment by order ID."""
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_transaction_id(
        self, transaction_id: str
    ) -> Payment | None:
        """Get payment by transaction ID."""
        result = await self.db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def process_payment(
        self, payment_data: PaymentProcessRequest, user_id: UUID
    ) -> Payment:
        """Process a payment for an order."""
        # Get the order
        order_service = OrderService(self.db)
        order = await order_service.get_order_by_id(payment_data.order_id)

        if not order:
            raise NotFoundError("Order", str(payment_data.order_id))

        # Verify order belongs to user
        if order.user_id != user_id:
            raise BadRequestError("Order does not belong to user")

        # Check if order is in valid state for payment
        if order.status != OrderStatus.PENDING:
            raise BadRequestError(
                f"Cannot process payment for order with status {order.status.value}"
            )

        # Check if payment already exists
        existing_payment = await self.get_payment_by_order_id(order.id)
        if existing_payment and existing_payment.status == PaymentStatus.COMPLETED:
            raise BadRequestError("Order has already been paid")

        # Process payment through gateway
        gateway_response = payment_gateway.process_payment(
            amount=order.total_amount,
            method=payment_data.method,
            card_number=payment_data.card_number,
            card_expiry=payment_data.card_expiry,
            card_cvv=payment_data.card_cvv,
            card_holder_name=payment_data.card_holder_name,
        )

        # Create or update payment record
        if existing_payment:
            payment = existing_payment
        else:
            payment = Payment(
                order_id=order.id,
                amount=order.total_amount,
                method=payment_data.method,
            )
            self.db.add(payment)

        if gateway_response.success:
            payment.status = PaymentStatus.COMPLETED
            payment.transaction_id = gateway_response.transaction_id
            payment.paid_at = datetime.utcnow()
            payment.gateway_response = gateway_response.raw_response

            # Update order status to confirmed
            order.status = OrderStatus.CONFIRMED
        else:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = gateway_response.message
            payment.gateway_response = gateway_response.raw_response

        await self.db.flush()
        await self.db.refresh(payment)

        return payment

    async def process_refund(
        self, payment_id: UUID, refund_data: RefundRequest
    ) -> Payment:
        """Process a refund for a payment."""
        payment = await self.get_payment_by_id(payment_id)

        if not payment:
            raise NotFoundError("Payment", str(payment_id))

        if not payment.can_refund:
            raise BadRequestError("This payment cannot be refunded")

        # Determine refund amount
        max_refundable = payment.amount - payment.refunded_amount
        refund_amount = refund_data.amount or max_refundable

        if refund_amount > max_refundable:
            raise BadRequestError(
                f"Refund amount exceeds maximum refundable: {max_refundable}"
            )

        # Process refund through gateway
        gateway_response = payment_gateway.process_refund(
            transaction_id=payment.transaction_id or "",
            amount=refund_amount,
            reason=refund_data.reason,
        )

        if gateway_response.success:
            payment.refunded_amount += refund_amount
            payment.refunded_at = datetime.utcnow()

            # Update payment status based on refund amount
            if payment.refunded_amount >= payment.amount:
                payment.status = PaymentStatus.REFUNDED
                # Update order status
                order_service = OrderService(self.db)
                order = await order_service.get_order_by_id(payment.order_id)
                if order:
                    order.status = OrderStatus.REFUNDED
            else:
                payment.status = PaymentStatus.PARTIALLY_REFUNDED

            # Store refund transaction details
            refund_info = payment.gateway_response or {}
            refund_info["refund_transaction_id"] = gateway_response.transaction_id
            refund_info["refund_reason"] = refund_data.reason
            payment.gateway_response = refund_info
        else:
            raise BadRequestError(f"Refund failed: {gateway_response.message}")

        await self.db.flush()
        await self.db.refresh(payment)

        return payment

    def get_available_payment_methods(self) -> list[dict]:
        """Get list of available payment methods."""
        return [
            {
                "method": PaymentMethod.CREDIT_CARD,
                "name": "Credit Card",
                "description": "Pay securely with your credit card",
                "is_available": True,
            },
            {
                "method": PaymentMethod.DEBIT_CARD,
                "name": "Debit Card",
                "description": "Pay directly from your bank account",
                "is_available": True,
            },
            {
                "method": PaymentMethod.PAYPAL,
                "name": "PayPal",
                "description": "Pay with your PayPal account",
                "is_available": True,
            },
            {
                "method": PaymentMethod.BANK_TRANSFER,
                "name": "Bank Transfer",
                "description": "Direct bank transfer",
                "is_available": True,
            },
            {
                "method": PaymentMethod.CASH_ON_DELIVERY,
                "name": "Cash on Delivery",
                "description": "Pay when you receive your order",
                "is_available": True,
            },
        ]

    async def generate_invoice(self, order_id: UUID, user_id: UUID) -> dict:
        """Generate invoice data for an order."""
        order_service = OrderService(self.db)
        order = await order_service.get_order_by_id(order_id)

        if not order:
            raise NotFoundError("Order", str(order_id))

        # Verify order belongs to user or user is admin
        if order.user_id != user_id:
            raise BadRequestError("Order does not belong to user")

        # Get user info
        from src.auth.service import AuthService

        auth_service = AuthService(self.db)
        user = await auth_service.get_user_by_id(order.user_id)

        if not user:
            raise NotFoundError("User", str(order.user_id))

        # Build invoice items
        items = [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
            for item in order.items
        ]

        payment = await self.get_payment_by_order_id(order_id)

        return {
            "invoice_number": f"INV-{order.order_number}",
            "order_number": order.order_number,
            "customer_name": user.full_name,
            "customer_email": user.email,
            "billing_address": order.billing_address or order.shipping_address,
            "items": items,
            "subtotal": order.subtotal,
            "tax_amount": order.tax_amount,
            "shipping_amount": order.shipping_amount,
            "discount_amount": order.discount_amount,
            "total_amount": order.total_amount,
            "payment_method": payment.method.value if payment else "pending",
            "payment_status": payment.status.value if payment else "pending",
            "paid_at": payment.paid_at if payment else None,
            "created_at": order.created_at,
        }
