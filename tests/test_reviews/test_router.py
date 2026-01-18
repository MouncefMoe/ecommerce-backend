"""Tests for reviews router."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_create_review(client: AsyncClient, test_user, test_product, user_token):
    """Test create product review."""
    response = await client.post(
        "/api/v1/reviews",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "rating": 5,
            "title": "Great product!",
            "comment": "This is a really great product. I highly recommend it.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5
    assert data["title"] == "Great product!"
    assert data["user_id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_create_duplicate_review_fails(
    client: AsyncClient, test_user, test_product, user_token
):
    """Test creating duplicate review fails."""
    # Create first review
    await client.post(
        "/api/v1/reviews",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "rating": 5,
            "comment": "First review for this product, great!",
        },
    )

    # Try to create second review
    response = await client.post(
        "/api/v1/reviews",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "rating": 4,
            "comment": "Second review for this product, nice!",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_product_reviews(
    client: AsyncClient, test_user, test_product, user_token
):
    """Test list reviews for product."""
    # Create a review first
    await client.post(
        "/api/v1/reviews",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "rating": 4,
            "comment": "Good product for testing reviews.",
        },
    )

    # List reviews
    response = await client.get(
        f"/api/v1/reviews/product/{test_product.id}",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert "average_rating" in data


@pytest.mark.asyncio
async def test_update_review(client: AsyncClient, test_user, test_product, user_token):
    """Test update own review."""
    # Create review
    create_response = await client.post(
        "/api/v1/reviews",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "rating": 3,
            "comment": "Original review comment here.",
        },
    )
    review_id = create_response.json()["id"]

    # Update review
    response = await client.patch(
        f"/api/v1/reviews/{review_id}",
        headers=auth_header(user_token),
        json={
            "rating": 5,
            "comment": "Updated review - much better now!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5


@pytest.mark.asyncio
async def test_delete_review(client: AsyncClient, test_user, test_product, user_token):
    """Test delete own review."""
    # Create review
    create_response = await client.post(
        "/api/v1/reviews",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "rating": 2,
            "comment": "Review to be deleted later.",
        },
    )
    review_id = create_response.json()["id"]

    # Delete review
    response = await client.delete(
        f"/api/v1/reviews/{review_id}",
        headers=auth_header(user_token),
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_review_stats(
    client: AsyncClient, test_user, test_product, user_token
):
    """Test get review statistics for product."""
    # Create a review
    await client.post(
        "/api/v1/reviews",
        headers=auth_header(user_token),
        json={
            "product_id": str(test_product.id),
            "rating": 4,
            "comment": "Review for statistics testing.",
        },
    )

    # Get stats
    response = await client.get(
        f"/api/v1/reviews/product/{test_product.id}/stats",
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_reviews" in data
    assert "average_rating" in data
    assert "rating_distribution" in data
