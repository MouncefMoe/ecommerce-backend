"""Admin API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    DashboardStats,
    LowStockProduct,
    OrdersByStatus,
    SalesAnalytics,
    TopProduct,
)
from src.admin.service import AdminService
from src.auth.dependencies import AdminUser
from src.database import get_db
from src.orders.schemas import OrderResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStats:
    """Get dashboard statistics."""
    service = AdminService(db)
    return await service.get_dashboard_stats()


@router.get("/orders/by-status", response_model=OrdersByStatus)
async def get_orders_by_status(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrdersByStatus:
    """Get order counts grouped by status."""
    service = AdminService(db)
    return await service.get_orders_by_status()


@router.get("/analytics/sales", response_model=SalesAnalytics)
async def get_sales_analytics(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
) -> SalesAnalytics:
    """Get sales analytics for a period."""
    service = AdminService(db)
    return await service.get_sales_analytics(days=days)


@router.get("/analytics/top-products", response_model=list[TopProduct])
async def get_top_products(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
) -> list[TopProduct]:
    """Get top selling products."""
    service = AdminService(db)
    return await service.get_top_products(limit=limit)


@router.get("/products/low-stock", response_model=list[LowStockProduct])
async def get_low_stock_products(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    threshold: int = Query(10, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[LowStockProduct]:
    """Get products with low stock."""
    service = AdminService(db)
    return await service.get_low_stock_products(threshold=threshold, limit=limit)


@router.get("/orders/recent", response_model=list[OrderResponse])
async def get_recent_orders(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
) -> list[OrderResponse]:
    """Get recent orders."""
    service = AdminService(db)
    orders = await service.get_recent_orders(limit=limit)
    return [OrderResponse.model_validate(o) for o in orders]
