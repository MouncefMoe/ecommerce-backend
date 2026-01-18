"""Tests for products router."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, test_product):
    """Test list products."""
    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, test_product):
    """Test get single product."""
    response = await client.get(f"/api/v1/products/{test_product.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_product.name
    assert data["sku"] == test_product.sku


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    """Test get non-existent product."""
    from uuid import uuid4

    response = await client.get(f"/api/v1/products/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_product_as_seller(
    client: AsyncClient, test_seller, test_category, seller_token
):
    """Test seller can create product."""
    response = await client.post(
        "/api/v1/products",
        headers=auth_header(seller_token),
        json={
            "name": "New Product",
            "description": "A new test product",
            "price": "49.99",
            "stock": 50,
            "sku": "NEW-SKU-001",
            "category_id": test_category.id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Product"
    assert data["seller_id"] == str(test_seller.id)


@pytest.mark.asyncio
async def test_create_product_as_customer_fails(
    client: AsyncClient, test_user, test_category, user_token
):
    """Test customer cannot create product."""
    response = await client.post(
        "/api/v1/products",
        headers=auth_header(user_token),
        json={
            "name": "New Product",
            "description": "A new test product",
            "price": "49.99",
            "stock": 50,
            "sku": "NEW-SKU-002",
            "category_id": test_category.id,
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_product_as_owner(
    client: AsyncClient, test_product, test_seller, seller_token
):
    """Test seller can update own product."""
    response = await client.patch(
        f"/api/v1/products/{test_product.id}",
        headers=auth_header(seller_token),
        json={
            "name": "Updated Product Name",
            "price": "129.99",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Product Name"


@pytest.mark.asyncio
async def test_delete_product_as_owner(
    client: AsyncClient, test_product, seller_token
):
    """Test seller can delete own product."""
    response = await client.delete(
        f"/api/v1/products/{test_product.id}",
        headers=auth_header(seller_token),
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_filter_products_by_category(
    client: AsyncClient, test_product, test_category
):
    """Test filter products by category."""
    response = await client.get(
        f"/api/v1/products?category_id={test_category.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, test_product):
    """Test search products."""
    response = await client.get("/api/v1/products?q=Test")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


# Category tests
@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, test_category):
    """Test list categories."""
    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_category_as_admin(client: AsyncClient, admin_token):
    """Test admin can create category."""
    response = await client.post(
        "/api/v1/categories",
        headers=auth_header(admin_token),
        json={
            "name": "New Category",
            "description": "A new category",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Category"


@pytest.mark.asyncio
async def test_create_category_as_seller_fails(client: AsyncClient, seller_token):
    """Test seller cannot create category."""
    response = await client.post(
        "/api/v1/categories",
        headers=auth_header(seller_token),
        json={
            "name": "Another Category",
            "description": "Another category",
        },
    )
    assert response.status_code == 403
