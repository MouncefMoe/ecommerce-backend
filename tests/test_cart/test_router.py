"""Tests for cart router."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_get_empty_cart(client: AsyncClient, test_user, user_token):
    """Test get empty cart."""
    response = await client.get(
        "/api/v1/cart",
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert float(data["total"]) == 0
    assert data["item_count"] == 0


@pytest.mark.asyncio
async def test_add_item_to_cart(client: AsyncClient, test_user, test_product, user_token):
    """Test add item to cart."""
    response = await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 2,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["item_count"] == 2


@pytest.mark.asyncio
async def test_add_item_increases_quantity(
    client: AsyncClient, test_user, test_product, user_token
):
    """Test adding same item increases quantity."""
    # Add first time
    await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
    )

    # Add again
    response = await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 2,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["items"][0]["quantity"] == 3


@pytest.mark.asyncio
async def test_update_cart_item(client: AsyncClient, test_user, test_product, user_token):
    """Test update cart item quantity."""
    # Add item first
    add_response = await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
    )
    item_id = add_response.json()["items"][0]["id"]

    # Update quantity
    response = await client.patch(
        f"/api/v1/cart/items/{item_id}",
        headers=auth_header(user_token),
        json={"quantity": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_remove_cart_item(client: AsyncClient, test_user, test_product, user_token):
    """Test remove item from cart."""
    # Add item first
    add_response = await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
    )
    item_id = add_response.json()["items"][0]["id"]

    # Remove item
    response = await client.delete(
        f"/api/v1/cart/items/{item_id}",
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_clear_cart(client: AsyncClient, test_user, test_product, user_token):
    """Test clear entire cart."""
    # Add item first
    await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 3,
        },
    )

    # Clear cart
    response = await client.delete(
        "/api/v1/cart",
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_cart_requires_auth(client: AsyncClient):
    """Test cart endpoints require authentication."""
    response = await client.get("/api/v1/cart")
    assert response.status_code == 401
