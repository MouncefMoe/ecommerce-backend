"""Order service with business logic."""

import secrets
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.cart.service import CartService
from src.exceptions import BadRequestError, ForbiddenError, NotFoundError
from src.orders.models import Order, OrderItem, OrderStatus
from src.orders.schemas import OrderCreate, OrderStatusUpdate
from src.products.service import ProductService


def generate_order_number() -> str:
    """Generate a unique order number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"ORD-{timestamp}-{random_part}"


class OrderService:
    """Service for order operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order_by_id(self, order_id: UUID) -> Order | None:
        """Get order by ID."""
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment),
            )
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_order_by_number(self, order_number: str) -> Order | None:
        """Get order by order number."""
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment),
            )
            .where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def get_user_orders(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        """Get user's orders with pagination."""
        query = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment),
            )
            .where(Order.user_id == user_id)
        )

        if status:
            query = query.where(Order.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        orders = list(result.scalars().all())

        return orders, total

    async def get_all_orders(
        self,
        skip: int = 0,
        limit: int = 20,
        status: OrderStatus | None = None,
        user_id: UUID | None = None,
    ) -> tuple[list[Order], int]:
        """Get all orders with pagination (admin)."""
        query = select(Order).options(
            selectinload(Order.items),
            selectinload(Order.payment),
        )

        if status:
            query = query.where(Order.status == status)

        if user_id:
            query = query.where(Order.user_id == user_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        orders = list(result.scalars().all())

        return orders, total

    async def create_order_from_cart(
        self, user_id: UUID, order_data: OrderCreate
    ) -> Order:
        """Create a new order from user's cart."""
        # Validate cart
        cart_service = CartService(self.db)
        cart = await cart_service.validate_cart_for_checkout(user_id)

        # Calculate totals
        subtotal = cart.total
        tax_amount = Decimal("0.00")  # Can be calculated based on rules
        shipping_amount = Decimal("0.00")  # Can be calculated based on address
        discount_amount = Decimal("0.00")  # Can apply coupon discounts
        total_amount = subtotal + tax_amount + shipping_amount - discount_amount

        # Create order
        order = Order(
            order_number=generate_order_number(),
            user_id=user_id,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            shipping_address=order_data.shipping_address.model_dump(),
            billing_address=(
                order_data.billing_address.model_dump()
                if order_data.billing_address
                else None
            ),
            notes=order_data.notes,
        )

        self.db.add(order)
        await self.db.flush()

        # Create order items and update stock
        product_service = ProductService(self.db)

        for cart_item in cart.items:
            # Create order item with snapshot data
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=cart_item.product.name,
                product_sku=cart_item.product.sku,
                product_image_url=cart_item.product.image_url,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
            )
            self.db.add(order_item)

            # Decrease product stock
            await product_service.update_product_stock(
                cart_item.product_id, -cart_item.quantity
            )

        # Clear cart
        await cart_service.clear_cart(user_id)

        await self.db.flush()
        await self.db.refresh(order)

        return order

    async def update_order_status(
        self,
        order_id: UUID,
        status_data: OrderStatusUpdate,
        user_id: UUID | None = None,
        is_admin: bool = False,
    ) -> Order:
        """Update order status."""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise NotFoundError("Order", str(order_id))

        # Check authorization (if not admin, user must own the order)
        if not is_admin and order.user_id != user_id:
            raise ForbiddenError("Not authorized to update this order")

        new_status = status_data.status

        # Validate status transition
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [
                OrderStatus.PROCESSING,
                OrderStatus.CANCELLED,
            ],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
            OrderStatus.CANCELLED: [],
            OrderStatus.REFUNDED: [],
        }

        if new_status not in valid_transitions.get(order.status, []):
            raise BadRequestError(
                f"Cannot transition from {order.status.value} to {new_status.value}"
            )

        # Update status and related timestamps
        order.status = new_status

        if new_status == OrderStatus.CANCELLED:
            order.cancelled_at = datetime.utcnow()
            # Restore product stock
            await self._restore_order_stock(order)
        elif new_status == OrderStatus.SHIPPED:
            order.shipped_at = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
        elif new_status == OrderStatus.REFUNDED:
            # Restore product stock on refund
            await self._restore_order_stock(order)

        if status_data.notes:
            order.notes = (
                f"{order.notes}\n{status_data.notes}"
                if order.notes
                else status_data.notes
            )

        await self.db.flush()
        await self.db.refresh(order)

        return order

    async def cancel_order(
        self,
        order_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
        reason: str | None = None,
    ) -> Order:
        """Cancel an order."""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise NotFoundError("Order", str(order_id))

        # Check authorization
        if not is_admin and order.user_id != user_id:
            raise ForbiddenError("Not authorized to cancel this order")

        if not order.can_cancel:
            raise BadRequestError(
                f"Cannot cancel order with status {order.status.value}"
            )

        status_update = OrderStatusUpdate(
            status=OrderStatus.CANCELLED,
            notes=reason,
        )

        return await self.update_order_status(
            order_id, status_update, user_id, is_admin
        )

    async def _restore_order_stock(self, order: Order) -> None:
        """Restore product stock when order is cancelled or refunded."""
        product_service = ProductService(self.db)

        for item in order.items:
            if item.product_id:
                try:
                    await product_service.update_product_stock(
                        item.product_id, item.quantity
                    )
                except NotFoundError:
                    # Product may have been deleted
                    pass

    async def count_orders_by_status(self) -> dict[str, int]:
        """Count orders by status (for admin dashboard)."""
        result = await self.db.execute(
            select(Order.status, func.count(Order.id))
            .group_by(Order.status)
        )

        counts = {status.value: 0 for status in OrderStatus}
        for row in result:
            counts[row[0].value] = row[1]

        return counts

    async def get_total_revenue(self) -> Decimal:
        """Get total revenue from completed orders."""
        result = await self.db.execute(
            select(func.sum(Order.total_amount)).where(
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED])
            )
        )
        return result.scalar() or Decimal("0.00")
