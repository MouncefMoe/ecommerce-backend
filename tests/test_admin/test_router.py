"""Tests for admin router."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_get_dashboard(client: AsyncClient, test_admin, admin_token):
    """Test get admin dashboard."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_products" in data
    assert "total_orders" in data
    assert "total_revenue" in data


@pytest.mark.asyncio
async def test_dashboard_requires_admin(client: AsyncClient, test_user, user_token):
    """Test dashboard requires admin access."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers=auth_header(user_token),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_orders_by_status(client: AsyncClient, test_admin, admin_token):
    """Test get orders grouped by status."""
    response = await client.get(
        "/api/v1/admin/orders/by-status",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "confirmed" in data
    assert "shipped" in data
    assert "delivered" in data


@pytest.mark.asyncio
async def test_get_sales_analytics(client: AsyncClient, test_admin, admin_token):
    """Test get sales analytics."""
    response = await client.get(
        "/api/v1/admin/analytics/sales?days=30",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_orders" in data
    assert "total_revenue" in data
    assert "average_order_value" in data


@pytest.mark.asyncio
async def test_get_top_products(client: AsyncClient, test_admin, admin_token):
    """Test get top selling products."""
    response = await client.get(
        "/api/v1/admin/analytics/top-products?limit=10",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_low_stock_products(
    client: AsyncClient, test_admin, test_product, admin_token
):
    """Test get low stock products."""
    response = await client.get(
        "/api/v1/admin/products/low-stock?threshold=10",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_recent_orders(client: AsyncClient, test_admin, admin_token):
    """Test get recent orders."""
    response = await client.get(
        "/api/v1/admin/orders/recent?limit=10",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
