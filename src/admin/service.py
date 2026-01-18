"""Admin service with business logic."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    DashboardStats,
    LowStockProduct,
    OrdersByStatus,
    SalesAnalytics,
    TopProduct,
)
from src.auth.models import User, UserRole
from src.orders.models import Order, OrderItem, OrderStatus
from src.products.models import Product
from src.reviews.models import Review


class AdminService:
    """Service for admin dashboard operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics."""
        # User counts
        total_users_result = await self.db.execute(
            select(func.count(User.id))
        )
        total_users = total_users_result.scalar() or 0

        customers_result = await self.db.execute(
            select(func.count(User.id)).where(User.role == UserRole.CUSTOMER)
        )
        total_customers = customers_result.scalar() or 0

        sellers_result = await self.db.execute(
            select(func.count(User.id)).where(User.role == UserRole.SELLER)
        )
        total_sellers = sellers_result.scalar() or 0

        # Product counts
        total_products_result = await self.db.execute(
            select(func.count(Product.id))
        )
        total_products = total_products_result.scalar() or 0

        active_products_result = await self.db.execute(
            select(func.count(Product.id)).where(Product.is_active == True)
        )
        active_products = active_products_result.scalar() or 0

        # Order counts
        total_orders_result = await self.db.execute(
            select(func.count(Order.id))
        )
        total_orders = total_orders_result.scalar() or 0

        pending_orders_result = await self.db.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING)
        )
        pending_orders = pending_orders_result.scalar() or 0

        # Revenue
        revenue_result = await self.db.execute(
            select(func.sum(Order.total_amount)).where(
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED])
            )
        )
        total_revenue = revenue_result.scalar() or Decimal("0.00")

        # Pending reviews
        pending_reviews_result = await self.db.execute(
            select(func.count(Review.id)).where(Review.is_approved == False)
        )
        pending_reviews = pending_reviews_result.scalar() or 0

        return DashboardStats(
            total_users=total_users,
            total_customers=total_customers,
            total_sellers=total_sellers,
            total_products=total_products,
            active_products=active_products,
            total_orders=total_orders,
            pending_orders=pending_orders,
            total_revenue=total_revenue,
            pending_reviews=pending_reviews,
        )

    async def get_orders_by_status(self) -> OrdersByStatus:
        """Get order counts grouped by status."""
        result = await self.db.execute(
            select(Order.status, func.count(Order.id)).group_by(Order.status)
        )

        counts = {status: 0 for status in OrderStatus}
        for row in result:
            counts[row[0]] = row[1]

        return OrdersByStatus(
            pending=counts[OrderStatus.PENDING],
            confirmed=counts[OrderStatus.CONFIRMED],
            processing=counts[OrderStatus.PROCESSING],
            shipped=counts[OrderStatus.SHIPPED],
            delivered=counts[OrderStatus.DELIVERED],
            cancelled=counts[OrderStatus.CANCELLED],
            refunded=counts[OrderStatus.REFUNDED],
        )

    async def get_sales_analytics(self, days: int = 30) -> SalesAnalytics:
        """Get sales analytics for the given period."""
        from datetime import datetime, timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        # Get orders in period
        orders_result = await self.db.execute(
            select(
                func.count(Order.id).label("count"),
                func.sum(Order.total_amount).label("revenue"),
            ).where(
                Order.created_at >= start_date,
                Order.status.in_([
                    OrderStatus.CONFIRMED,
                    OrderStatus.PROCESSING,
                    OrderStatus.SHIPPED,
                    OrderStatus.DELIVERED,
                ])
            )
        )
        row = orders_result.one()

        total_orders = row.count or 0
        total_revenue = row.revenue or Decimal("0.00")
        avg_order_value = (
            total_revenue / total_orders if total_orders > 0 else Decimal("0.00")
        )

        orders_by_status = await self.get_orders_by_status()

        return SalesAnalytics(
            period=f"Last {days} days",
            total_orders=total_orders,
            total_revenue=total_revenue,
            average_order_value=avg_order_value,
            orders_by_status=orders_by_status,
        )

    async def get_top_products(self, limit: int = 10) -> list[TopProduct]:
        """Get top selling products."""
        result = await self.db.execute(
            select(
                OrderItem.product_id,
                OrderItem.product_name,
                func.sum(OrderItem.quantity).label("total_sold"),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
            )
            .join(Order)
            .where(
                Order.status.in_([OrderStatus.SHIPPED, OrderStatus.DELIVERED])
            )
            .group_by(OrderItem.product_id, OrderItem.product_name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )

        products = []
        for row in result:
            products.append(
                TopProduct(
                    product_id=str(row.product_id),
                    product_name=row.product_name,
                    total_sold=row.total_sold or 0,
                    total_revenue=row.revenue or Decimal("0.00"),
                )
            )

        return products

    async def get_low_stock_products(
        self, threshold: int = 10, limit: int = 20
    ) -> list[LowStockProduct]:
        """Get products with low stock."""
        result = await self.db.execute(
            select(Product, User.full_name)
            .join(User, Product.seller_id == User.id)
            .where(Product.stock <= threshold, Product.is_active == True)
            .order_by(Product.stock.asc())
            .limit(limit)
        )

        products = []
        for row in result:
            product = row[0]
            seller_name = row[1]
            products.append(
                LowStockProduct(
                    product_id=str(product.id),
                    product_name=product.name,
                    sku=product.sku,
                    current_stock=product.stock,
                    seller_name=seller_name,
                )
            )

        return products

    async def get_recent_orders(self, limit: int = 10) -> list[Order]:
        """Get recent orders."""
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payment))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())
