"""Tests for payments router."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_list_payment_methods(client: AsyncClient):
    """Test list available payment methods."""
    response = await client.get("/api/v1/payments/methods")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Check structure
    method = data[0]
    assert "method" in method
    assert "name" in method
    assert "description" in method


@pytest.mark.asyncio
async def test_process_payment_success(
    client: AsyncClient, test_user, test_product, user_token
):
    """Test process payment for order."""
    # Create order first
    await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
    )

    order_response = await client.post(
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
    order_id = order_response.json()["id"]

    # Process payment with test card that always succeeds
    response = await client.post(
        "/api/v1/payments/process",
        headers=auth_header(user_token),
        json={
            "order_id": order_id,
            "method": "credit_card",
            "card_number": "4242424242424242",
            "card_expiry": "12/25",
            "card_cvv": "123",
            "card_holder_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["transaction_id"] is not None


@pytest.mark.asyncio
async def test_process_payment_declined(
    client: AsyncClient, test_user, test_product, user_token
):
    """Test payment with declined card."""
    # Create order first
    await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
    )

    order_response = await client.post(
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
    order_id = order_response.json()["id"]

    # Process payment with test card that always declines
    response = await client.post(
        "/api/v1/payments/process",
        headers=auth_header(user_token),
        json={
            "order_id": order_id,
            "method": "credit_card",
            "card_number": "4000000000000002",
            "card_expiry": "12/25",
            "card_cvv": "123",
            "card_holder_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "failed"


@pytest.mark.asyncio
async def test_get_invoice(
    client: AsyncClient, test_user, test_product, user_token
):
    """Test get invoice for order."""
    # Create and pay for order
    await client.post(
        "/api/v1/cart/items",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "quantity": 1,
        },
    )

    order_response = await client.post(
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
    order_id = order_response.json()["id"]

    await client.post(
        "/api/v1/payments/process",
        headers=auth_header(user_token),
        json={
            "order_id": order_id,
            "method": "credit_card",
            "card_number": "4242424242424242",
            "card_expiry": "12/25",
            "card_cvv": "123",
        },
    )

    # Get invoice
    response = await client.get(
        f"/api/v1/payments/order/{order_id}/invoice",
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert "invoice_number" in data
    assert "items" in data
    assert "total_amount" in data
