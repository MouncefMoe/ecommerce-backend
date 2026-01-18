"""Tests for orders router."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_list_orders_empty(client: AsyncClient, test_user, user_token):
    """Test list orders when empty."""
    response = await client.get(
        "/api/v1/orders",
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_order_empty_cart(client: AsyncClient, test_user, user_token):
    """Test creating order with empty cart fails."""
    response = await client.post(
        "/api/v1/orders",
        headers=auth_header(user_token),
        json={
            "shipping_address": {
                "full_name": "Test User",
                "phone": "1234567890",
                "address_line1": "123 Test St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "Test Country",
            }
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_order_success(
    client: AsyncClient, test_user, test_product, user_token
):
    """Test create order from cart."""
    # First add item to cart
    await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 2,
        },
    )

    # Create order
    response = await client.post(
        "/api/v1/orders",
        headers=auth_header(user_token),
        json={
            "shipping_address": {
                "full_name": "Test User",
                "phone": "1234567890",
                "address_line1": "123 Test St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "Test Country",
            }
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert len(data["items"]) == 1
    assert data["item_count"] == 2


@pytest.mark.asyncio
async def test_get_order(client: AsyncClient, test_user, test_product, user_token):
    """Test get order by ID."""
    # Create order first
    await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
    )

    create_response = await client.post(
        "/api/v1/orders",
        headers=auth_header(user_token),
        json={
            "shipping_address": {
                "full_name": "Test User",
                "phone": "1234567890",
                "address_line1": "123 Test St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "Test Country",
            }
        },
    )
    order_id = create_response.json()["id"]

    # Get order
    response = await client.get(
        f"/api/v1/orders/{order_id}",
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id


@pytest.mark.asyncio
async def test_cancel_order(client: AsyncClient, test_user, test_product, user_token):
    """Test cancel order."""
    # Create order first
    await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
    )

    create_response = await client.post(
        "/api/v1/orders",
        headers=auth_header(user_token),
        json={
            "shipping_address": {
                "full_name": "Test User",
                "phone": "1234567890",
                "address_line1": "123 Test St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "Test Country",
            }
        },
    )
    order_id = create_response.json()["id"]

    # Cancel order
    response = await client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_orders_require_auth(client: AsyncClient):
    """Test orders endpoints require authentication."""
    response = await client.get("/api/v1/orders")
    assert response.status_code == 401
