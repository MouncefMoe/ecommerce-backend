"""Pydantic schemas for admin dashboard."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""

    total_users: int
    total_customers: int
    total_sellers: int
    total_products: int
    active_products: int
    total_orders: int
    pending_orders: int
    total_revenue: Decimal
    pending_reviews: int


class OrdersByStatus(BaseModel):
    """Schema for orders grouped by status."""

    pending: int
    confirmed: int
    processing: int
    shipped: int
    delivered: int
    cancelled: int
    refunded: int


class SalesAnalytics(BaseModel):
    """Schema for sales analytics."""

    period: str
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    orders_by_status: OrdersByStatus


class RevenueByPeriod(BaseModel):
    """Schema for revenue by time period."""

    date: str
    revenue: Decimal
    order_count: int


class TopProduct(BaseModel):
    """Schema for top selling product."""

    product_id: str
    product_name: str
    total_sold: int
    total_revenue: Decimal


class UserGrowth(BaseModel):
    """Schema for user growth metrics."""

    date: str
    new_users: int
    cumulative_users: int


class LowStockProduct(BaseModel):
    """Schema for low stock product alert."""

    product_id: str
    product_name: str
    sku: str
    current_stock: int
    seller_name: str
